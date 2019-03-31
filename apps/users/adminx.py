# users/adminx.py
__author__ = 'jourminyan'

import xadmin
from xadmin import views
from .models import VerifyCode


class BaseSetting(object):
    # enable themes
    enable_themes = True
    use_bootswatch = True


class GlobalSettings(object):
    site_title = "旧爱运动"
    site_footer = "https://www.carbrands.club/carbrands/"
    # left menu in
    menu_style = "accordion"


class VerifyCodeAdmin(object):
    list_display = ['code', 'mobile', "add_time"]


xadmin.site.register(VerifyCode, VerifyCodeAdmin)
xadmin.site.register(views.BaseAdminView, BaseSetting)
xadmin.site.register(views.CommAdminView, GlobalSettings)
