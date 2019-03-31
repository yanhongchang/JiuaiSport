from django.shortcuts import render

__author__ = "jourminyan"


from random import choice
import requests
import json
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, RetrieveModelMixin
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_jwt.serializers import jwt_encode_handler, jwt_payload_handler
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework import permissions
from rest_framework import authentication

from qcloudsms_py import SmsSingleSender
from qcloudsms_py.httpclient import HTTPError

from JiuaiSport.settings import SMSAPPID, APPKEY, SMS_TEMPLATE, SMS_SIGN
from JiuaiSport.settings import APPID, APPSECRET
from .serializers import SmsSerializer, UserRegSerializer, UserDetailSerializer, WXUserRegSerializer, \
    UserMobileBindingSerializer
from .models import VerifyCode
from .WXBizDataCrypt import WXBizDataCrypt

User = get_user_model()


class CustomBackend(ModelBackend):
    """自定义用户验证后端"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(
                Q(username=username) | Q(mobile=username))
            if user.check_password(password):
                return user
        except Exception as e:
            return None


class WXUserView(APIView):

    def post(self, request):
        opendata = request.data
        print(opendata)
        code = opendata["code"]
        encrypteddata = opendata["encryptedData"]
        iv = opendata["iv"]
        sessiondata = self.code2session(code)
        print(sessiondata)

        if sessiondata.get("errcode", 0) == 0:
            pc = WXBizDataCrypt(APPID, sessiondata["session_key"])
        else:
            print('sorry, get session key error, the err code is %s ' % sessiondata["errcode"])
        return Response(pc.decrypt(encrypteddata, iv))

    def code2session(self, code):
        url = "https://api.weixin.qq.com/sns/jscode2session?appid=" + APPID+"&secret=" + APPSECRET + \
              "&js_code=" + code + "&grant_type=authorization_code"
        print(url)
        sessiondata = requests.get(url)
        sessiondata_dict = json.loads(bytes.decode(sessiondata.content))
        return sessiondata_dict


class SmsCodeViewset(CreateModelMixin, viewsets.GenericViewSet):

    serializer_class = SmsSerializer

    @staticmethod
    def generate_code():
        """生成四位数字验证码"""
        seeds = "1234567890"
        random_str = []
        for i in range(4):
            random_str.append(choice(seeds))

        return "".join(random_str)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mobile = serializer.validated_data["mobile"]

        # 验证码
        code = self.generate_code()

        ssender = SmsSingleSender(SMSAPPID, APPKEY)
        params = [code, 5]
        try:
            sms_status = ssender.send_with_param(86, mobile, SMS_TEMPLATE, params, sign=SMS_SIGN, extend="", ext="")
            if sms_status["result"] != 0:
                return Response({
                    "mobile": sms_status["errmsg"]
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                code_record = VerifyCode(code=code, mobile=mobile)
                code_record.save()
                return Response({
                    "mobile": mobile
                }, status=status.HTTP_201_CREATED)

        except HTTPError as e:
            print(e)
        except Exception as e:
            print(e)


class WXUserViewset(CreateModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    """微信用户"""
    serializer_class = WXUserRegSerializer
    queryset = User.objects.all()
    authentication_classes = (JSONWebTokenAuthentication, authentication.SessionAuthentication)

    @staticmethod
    def code2session(code):
        url = "https://api.weixin.qq.com/sns/jscode2session?appid=" + APPID+"&secret=" + APPSECRET + \
              "&js_code=" + code + "&grant_type=authorization_code"
        print(url)
        session_data = requests.get(url)
        session_data_dict = json.loads(bytes.decode(session_data.content))
        return session_data_dict

    def get_wxuserinfo(self, req):
        opendata = req.data
        print(opendata)
        code = opendata["code"]
        encrypteddata = opendata["encryptedData"]
        iv = opendata["iv"]
        wxsession = self.code2session(code)

        if wxsession.get("errcode", 0) == 0:
            pc = WXBizDataCrypt(APPID, wxsession["session_key"])
        else:
            print('sorry, get session key error, the err code is %s ' % wxsession["errcode"])
        opendata = pc.decrypt(encrypteddata, iv)
        return opendata

    def create(self, request, *args, **kwargs):

        opendata = self.get_wxuserinfo(request)
        serializer = self.get_serializer(data=opendata)

        try:
            serializer.is_valid(raise_exception=True)

        except Exception as e:
            print(e)
        user = self.perform_create(serializer)

        # 赋值给一个列表
        re_dict = serializer.data

        re_dict["token"] = self.gen_token(user)
        re_dict["nickName"] = user.nickName
        re_dict["openId"] = user.openId

        headers = self.get_success_headers(serializer.data)

        return Response(re_dict, status=status.HTTP_201_CREATED, headers=headers)

    # 生成token加密
    @staticmethod
    def gen_token(user):
        payload = jwt_payload_handler(user)
        return jwt_encode_handler(payload)

    # 这里需要动态权限配置
    # 1.用户注册的时候不应该有权限限制
    # 2.当想获取用户详情信息的时候，必须登录才行
    def get_permissions(self):
        if self.action == "retrieve":
            return [permissions.IsAuthenticated()]
        elif self.action == "create":
            return []

        return []

    # 这里需要动态选择用哪个序列化方式
    # 1.WXUserRegSerializer（微信用户注册）用于新用户第一次登录注册。但是当老用户登录退出后再登录时，就不需要再次注册到数数据库，
    # 所以要创建一个WXUserloginSerializer
    # 2.问题又来了，如果注册的使用userdetailSerializer，又会导致验证失败，所以需要动态的使用serializer
    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserDetailSerializer
        elif self.action == "create":
            return UserRegSerializer

        return UserDetailSerializer


    # 虽然继承了Retrieve可以获取用户详情，但是并不知道用户的id，所有要重写get_object方法
    # 重写get_object方法，就知道是哪个用户了
    def get_object(self):
        return self.request.user

    def perform_create(self, serializer):
        return serializer.save()



class UserMobileBindViewset(UpdateModelMixin, viewsets.GenericViewSet):
    """微信用户"""
    serializer_class = UserMobileBindingSerializer
    lookup_field = 'username'

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
