from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User

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