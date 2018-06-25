# 序列化器
from django_redis import get_redis_connection
from redis import RedisError
from rest_framework import serializers
import logging

# 获取在配置文件中定义的logger，用来记录日志
logger = logging.getLogger('django')


class ImageCodeCheckSerializer(serializers.Serializer):
    """
    图片验证码校验序列化器
    """
    # UUIDField专门用于校验UUID类型的字符串
    image_code_id = serializers.UUIDField()
    image_code = serializers.CharField(min_length=4, max_length=4)

    def validate(self, attrs):
        # 校验
        # 接收具体的数值
        image_code_id = attrs['image_code_id']
        image_code = attrs['image_code']
        # 查询真实图片验证码
        redis_conn = get_redis_connection('verify_codes')
        real_image_code_text = redis_conn.get('img_%s' % image_code_id)
        if not real_image_code_text:
            raise serializers.ValidationError('图片验证码无效')

        # 删除图片验证码
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except RedisError as e:
            # 如果出现redis的异常，记录日志
            logger.error(e)

        # 比较图片验证码
        real_image_code_text = real_image_code_text.decode()
        if real_image_code_text.lower() != image_code.lower():
            raise serializers.ValidationError('图片验证码错误')

        # 判断是否在60秒内
        mobile = self.context['view'].kwargs['mobile']
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            raise serializers.ValidationError('请求次数过于频繁')

        return attrs
