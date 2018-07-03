import logging

from celery_tasks.main import app
from .yuntongxun.sms import CCP
from . import constants

# 获取在配置文件中定义的logger，用来记录日志
logger = logging.getLogger('django')

@app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    """
    发送短信验证码

    :return:
    """
    try:
        time = str(constants.SMS_CODE_REDIS_EXPIRES / 60)
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_TEMP_ID)
    except Exception as e:
        logger.error("发送验证码短信[异常][mobile: %s, message: %s ]" % mobile, e)
    else:
        if result == 0:
            logger.info("发送短信验证码[正常][mobile: %s]" % mobile)
        else:
            logger.warning("发送验证码短信[失败][ mobile: %s ]" % mobile)
