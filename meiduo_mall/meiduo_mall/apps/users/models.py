from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer, BadData


# Create your models here.
from meiduo_mall.utils.models import BaseModel
from vertifications import constants


class User(AbstractUser):
    """用户模型类"""
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='默认地址')

    # 用户信息
    def generate_send_sms_code_token(self):
        """
        生成发送短信验证码的token
        :return:
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.PASSWORD_TOKEN_EXPIRES)  # constants.SEND_SMS_TOKEN_EXPIRES=300
        data = {'mobile': self.mobile}
        token = serializer.dumps(data)
        return token.decode()

    @staticmethod
    def check_send_sms_code_token(token):
        """
        检验发送短信验证码的token
        :return:
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, constants.PASSWORD_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            return data.get('mobile')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


    def generate_sms_password_token(self):
        """
        生成修改密码的token
        :return:
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, constants.PASSWORD_TOKEN_EXPIRES)
        data = {'user_id': self.id}
        token = serializer.dumps(data)
        token = token.decode()
        return token

    @staticmethod
    def check_set_password_token(access_token):
        """
        检验设置密码的token
        :param token:
        :param user_id:
        :return:
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, constants.PASSWORD_TOKEN_EXPIRES)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return False
        else:
            return data.get('user_id')


    def generate_verify_email_url(self):
        """
        生成验证邮箱的url
        :return:
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
        data = {'user_id':self.id, 'email': self.email}
        token = serializer.dumps(data).decode()
        return token

    @staticmethod
    def check_verify_email_token(access_token):
        """校验激活邮件的access_token"""
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        else:
            # 获取用户
            email = data.get('email')
            user_id = data.get('user_id')
            try:
                user = User.objects.get(id=user_id, email=email)
            except User.DoesNotExist:
                return None
            return user


class Address(BaseModel):
    """
    用户地址
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('areas.Areas', on_delete=models.PROTECT, related_name='province_addresses',
                                 verbose_name='省')
    city = models.ForeignKey('areas.Areas', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Areas', on_delete=models.PROTECT, related_name='district_addresses',
                                 verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']