import re

from django.contrib.auth import mixins

# Create your views here.
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, GenericAPIView, UpdateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from users import serializers, constants
from users.utils import get_user_by_account
from .models import User
from vertifications.serializers import ImageCodeCheckSerializer


class UsernameCountView(APIView):
    """
    用户名数量
    """

    def get(self, request, username):
        # 获取指定用户数量
        count = User.objects.filter(username=username).count()
        data = {
            'username': username,
            'count': count
        }

        return Response(data)


class MobileCountView(APIView):
    """
    用户名数量
    """

    def get(self, request, mobile):
        # 获取指定用户数量
        count = User.objects.filter(mobile=mobile).count()
        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)


class UserView(CreateAPIView):
    """
    用户注册
    """
    serializer_class = serializers.CreateUserSerializer


class SMSCodeTokenView(GenericAPIView):
    """
    根据账号和验证码获取发送短信的访问令牌[access_token]
    """
    serializer_class = ImageCodeCheckSerializer

    def get(self, request, account):
        # 校验图形验证码
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 根据用户信息来查询用户
        user = get_user_by_account(account)
        if user is None:
            return Response({'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 生成一个access_token
        access_token = user.generate_send_sms_code_token()

        # 处理手机号
        mobile = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', user.mobile)
        return Response({'mobile': mobile, 'access_token': access_token})


class PasswordTokenView(GenericAPIView):
    """
    凭借短信验证码获取重置密码的access_token
    """
    serializer_class = serializers.CheckSMSCodeSerializer

    def get(self, request, account):
        """
        根据用户账号获取修改密码的token
        :param request:
        :param account:
        :return:
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = serializer.user

        # 生成修改用户密码的access_token
        access_token = user.generate_sms_password_token()
        return Response({'user_id': user.id, 'access_token': access_token})


class PasswordView(UpdateAPIView):
    """
    用户密码
    """
    queryset = User.objects.all()
    serializer_class = serializers.ResetPasswordSerializer

    def post(self, request, pk):
        return self.update(request, pk)


# RetrieveAPIView 继承了GenericAPIView， RetrieveModelMixin
class UserDetailView(RetrieveAPIView):
    """
    用户详情
    """
    serializer_class = serializers.UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    # 保存用户邮箱信息
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.EmailSerializer

    # 为了使视图的create方法在对序列化器进行save操作时执行序列化器的update方法，更新user的email属性
    # 所以重写get_serializer方法，在构造序列化器时，将请求的user对象传入
    # 在视图中，可以通过视图对象self中的request属性获取请求对象
    def get_object(self):
        return self.request.user


class VerifyEmailView(APIView):
    """
    判断激活邮件的token是否有效
    """

    def get(self, request):
        # 获取token
        token = request.query_params.get('token')
        # 校验token
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message': '无效的token'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.email_active = True
            user.save()

            return Response({'message': 'OK'})


class AddressViewSet(ModelViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = serializers.UserAddressSerializer
    permissions = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        queryset = self.get_queryset()
        serializer = serializers.UserAddressSerializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """保存用户地址数据"""
        # 检查用户地址数据不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存用户地址数已达上限'}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """处理删除"""
        address = self.get_object()
        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None, address_id=None):
        """设置默认地址"""
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None, address_id=None):
        """修改标题"""
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(isinstance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
