from django.db import models

__author__ = 'jourminyan'

from datetime import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser


class UserProfile(AbstractUser):
    """ user info """
    GENDER_CHOICES = (
        (1, u"男"),
        (0, u"女"),
    )
    # username、birthday、email can None when register by mobile verifyCode
    nickName = models.CharField("用户名", max_length=32, null=True, blank=True)
    birthday = models.DateField("出生年月", null=True, blank=True)
    gender = models.CharField("性别", max_length=8, choices=GENDER_CHOICES, default=1)
    mobile = models.CharField("电话", max_length=11, null=True, blank=True)
    country = models.CharField("国家", max_length=32, null=True, blank=True)
    city = models.CharField("城市", max_length=16, null=True, blank=True)
    province = models.CharField("省份", max_length=16, null=True, blank=True)
    avatarUrl = models.CharField("头像", max_length=128, null=True, blank=True)
    unionId = models.CharField("城市", max_length=16, null=True, blank=True)
    email = models.CharField("邮箱", max_length=128, null=True, blank=True)
    password = models.CharField("密码", max_length=128, null=True, blank=True)
    openId = models.CharField("微信openid", max_length=64, null=False, blank=False)

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class VerifyCode(models.Model):
    """ VerifyCode """
    code = models.CharField("验证码", max_length=8)
    mobile = models.CharField("电话号码", max_length=11)
    add_time = models.DateTimeField("添加时间", default=datetime.now)

    class Meta:
        verbose_name = "短信验证"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.code

