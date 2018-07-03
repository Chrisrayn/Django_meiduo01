import random

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection

from meiduo_mall.libs.yuntongxun.sms import CCP
from . import serializers
from meiduo_mall.apps.vertifications import constants
from meiduo_mall.libs.captcha.captcha import captcha
from celery_tasks.sms.tasks import send_sms_code


class ImageCodeView(APIView):
    """
    图片验证码
    """

    def get(self, request, image_code_id):
        # 生成验证码图片
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection("verify_codes")
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        return HttpResponse(image, content_type="images/jpg")


class SMSCodeView(GenericAPIView):
    """
    短信验证码
    """
    # 给当前视图类指定序列化器
    serializer_class = serializers.ImageCodeCheckSerializer

    def get(self, request, mobile):
        # 1，调用检查图片验证码的序列化器
        # data指定的就是序列化器中的validate中的attr属性
        # 通过 request.query_params 可以获取到？后面的查询字符串和字典
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # 检查图片验证码
        # 检查是否在60s内有发送记录
        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        # 保存短信验证码与发送记录
        redis_conn = get_redis_connection('verify_codes')
        pl = redis_conn.pipeline()
        pl.multi()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        #
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()
        # 发送短信验证码
        # time = str(constants.SMS_CODE_REDIS_EXPIRES / 60)
        # ccp = CCP()
        # ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_TEMP_ID)
        # 调用celer执行异步任务
        send_sms_code.delay(mobile, sms_code)
        # 返回响应结果
        return Response({"message": "ok"}, status.HTTP_200_OK)


class SMSCodeByTokenView(GenericAPIView):
    # 给当前视图类指定序列化器
    serializer_class = serializers.CheckSMSCodeTokenSerializer
    # 凭借access_token发送短信验证码

    def get(self, request):
        # 调用检验发送短信的access_token和手机号
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # 提取序列化器中的属性
        mobile = serializer.mobile

        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        # 保存短信验证码与发送记录
        redis_conn = get_redis_connection('verify_codes')
        pl = redis_conn.pipeline()
        pl.multi()
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()
        # 发送短信
        send_sms_code.delay(mobile,sms_code)
        # 返回响应结果
        return Response({'message': 'OK'}, status.HTTP_200_OK)

