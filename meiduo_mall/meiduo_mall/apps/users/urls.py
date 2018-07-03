from django.conf.urls import url
from . import views
from rest_framework_jwt.views import obtain_jwt_token

urlpatterns = [
    url(r'usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
    url(r'mobiles/(?P<mobile>1[345789]\d{9})/count/$', views.MobileCountView.as_view()),
    url(r'users/$', views.UserView.as_view()),
    # 用户登录
    url(r'authorizations/', obtain_jwt_token, name='authorizations'),
    #
    url(r'accounts/(?P<account>\w{5,20})/sms/token/$', views.SMSCodeTokenView.as_view()),
    url(r'accounts/(?P<account>\w{5,20})/password/token/$', views.PasswordTokenView.as_view()),
    url(r'users/(?P<pk>\d+)/password/$', views.PasswordView.as_view()),
    url(r'^user/$', views.UserDetailView.as_view()),
    url(r'emails/$', views.EmailView.as_view()),
    url(r'emails/verification/$', views.VerifyEmailView.as_view()),
    ]

