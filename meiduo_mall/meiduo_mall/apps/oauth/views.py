from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from oauth.exceptions import QQAPIError
from oauth.models import OAuthQQUser
from oauth.serializers import OAuthQQUserSerializer
from oauth.utils import OAuthQQ


class QQAuthURLView(APIView):
    """
    获取QQ登录的URL
    """

    def get(self, request):
        # 获取登录页面中，登录成功以后跳转的地址
        next = request.query_params.get('state')
        if not next:
            next = '/'

        oauth_qq = OAuthQQ()
        # 组装QQ登录url地址
        auth_url = oauth_qq.generate_qq_login_url(next)
        # 响应
        return Response({'auth_url': auth_url})


class QQAuthUserView(GenericAPIView):
    """
    QQ登录的用户
    """

    def get(self, request):
        # 接收code
        code = request.query_params.get('code')
        if not code:
            print('1111111')
            return Response({'message': '缺少code'}, status=status.HTTP_400_BAD_REQUEST)
            print('1111111')

        oauth = OAuthQQ()

        # 获取用户openid
        try:
            access_token = oauth.get_qq_access_token(code)
            openid = oauth.get_qq_openid(access_token)
        except QQAPIError:
            return Response({'message': 'QQ服务异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 凭借openid到OAuthQQUser模型，判断是否是第一次登录
        try:
            oauth_qq_user = OAuthQQUser.objects.get(openid=openid)
        except:
            token = OAuthQQUser.generate_save_user_token(openid)
            return Response({'access_token': token})
        else:
            # 不是第一次登录
            user = oauth_qq_user.user

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 载荷配置
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 生成token配置

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            return Response({
                'token': token,
                'username': user.username,
                'user_id': user.id
            })


    # 登录用户的qq
    serializer_class = OAuthQQUserSerializer

    def post(self, request):
        """
        保存qq登录用户数据
        :param request:
        :return:
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 生成已登录的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        return Response({
            'token': token,
            'username': user.username,
            'user_id': user.id,
        })



