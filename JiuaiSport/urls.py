"""JiuaiSport URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# from django.contrib import admin
from django.urls import path, include, re_path
import xadmin
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter

from users.views import *

router = DefaultRouter()

# 手机验证码
router.register(r'code', SmsCodeViewset, base_name="code")

# 用户的操作
#router.register(r'users', UserViewset, base_name="users")

# 微信用户登录注册操作
router.register(r'wxusers', WXUserViewset, base_name="wxusers")
router.register(r'wxusers', WXUserViewset, base_name="wxusers")

# 微信用户短信绑定操作
router.register(r'mobile', UserMobileBindViewset, base_name='wxmobile')

urlpatterns = [
    path('xadmin/', xadmin.site.urls),
    path('docs', include_docs_urls(title='旧爱运动')),
    path('api-auth/', include('rest_framework.urls')),
    path('ueditor/', include('DjangoUeditor.urls')),
    # 登录
    path('login/', obtain_jwt_token),
    re_path('^', include(router.urls)),
    path('wxusers/', WXUserView.as_view()),

]
