from django_redis import get_redis_connection
from rest_framework import serializers
import re
from rest_framework_jwt.settings import api_settings

from users.utils import get_user_by_account
from .models import User, Address
from celery_tasks.email.tasks import send_verify_email


# 创建序列化器对象
class CreateUserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(label='确认密码', required=True, allow_null=False, allow_blank=False, write_only=True)
    sms_code = serializers.CharField(label='短信验证码', required=True, allow_null=False, allow_blank=False, write_only=True)
    allow = serializers.CharField(label='同意协议', required=True, allow_null=False, allow_blank=False, write_only=True)
    # 增加一个token字段
    token = serializers.CharField(label='登录状态token', read_only=True)


    def validate_mobile(self, value):
        # 验证手机号
        if not re.match(r'^1[345789]\d{9}$', value):
            raise serializers.ValidationError('手机号码格式错误')
        return value

    def validate_allow(self, value):
        # 检验用户是否同意协议
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, data):
        # 判断两次密码
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 判断短信验证码
        redis_conn = get_redis_connection('verify_codes')
        mobile = data['mobile']

        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data

    def create(self, validated_data):
        """
        创建用户
        """
        # 移除数据库模型类中不存在的数据
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        user = super().create(validated_data)

        # 调用Django的认证系统加密密码
        user.set_password(validated_data['password'])
        user.save()

        # 补充生成记录登录状态的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        return user


    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow', 'token')
        extra_kwargs = {
            'id': {'read_only': True},
            'user_name':{
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password':{
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }


class CheckSMSCodeSerializer(serializers.Serializer):
    """
    检查sms code
    """
    sms_code = serializers.CharField(label='短信验证码', max_length=6, min_length=6)

    def validate(self, attrs):
        sms_code = attrs['sms_code']
        account = self.context['view'].kwargs.get('account')
        # 获取user
        user = get_user_by_account(account)
        if user is None:
            raise serializers.ValidationError('用户不存在')

        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % user.mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if sms_code != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        self.user = user

        return attrs


class ResetPasswordSerializer(serializers.ModelSerializer):
    """
    重置密码序列化器
    """
    password2 = serializers.CharField(label='确认密码', write_only=True)
    access_token = serializers.CharField(label='重置密码的access_token', write_only=True)

    class Meta:
        model = User
        fields = ('id', 'password', 'password2', 'access_token')
        extra_kwargs = {
            'password':{
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8 - 20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate(self, attrs):
        """
        校验数据
        :param attrs:
        :return:
        """
        # 判断两次密码
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次密码不一致')
        # 判断access_token
        allow = User.check_set_password_token(attrs['access_token'])
        if not allow:
            raise serializers.ValidationError('无效的access_token')
        return attrs


    def update(self, instance, validated_data):
        """
        更新密码
        :param instance:当前pk值对应的User模型对象
        :param validated_data:校验完成以后的数据
        :return:user对象
        """
        # 调用django用户模型类的设置密码方法
        instance.set_password(validated_data['password'])
        instance.save()
        return instance


class UserDetailSerializer(serializers.ModelSerializer):
    """
    用户详细信息序列化器
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'email_active')


class EmailSerializer(serializers.ModelSerializer):
    """
    邮箱序列化器
    """
    class Meta:
        model = User
        fields = ('id', 'email')
        extra_kwargs = {
            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        instance.email = validated_data['email']
        instance.save()

        # 生成验证链接
        token = instance.generate_verify_email_url()
        verify_url = "http://www.meiduo.com:8080/success_verify_email.html?token=" + token
        # 调用celery通过异步发送验证邮件
        send_verify_email.delay([instance.email], verify_url)

        return instance


class UserAddressSerializer(serializers.ModelSerializer):
    """
    用户地址序列化器
    """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def create(self, validated_data):
        """保存"""
        # Address模型类中有user属性，将user对象添加到模型类的创建参数中
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressTitleSerializer():
    """地址标题"""
    class Meta:
        model = Address
        fields = ('title',)