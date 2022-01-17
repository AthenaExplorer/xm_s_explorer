import string, random, datetime
from xm_s_common import inner_server, consts
from django.db import transaction
from pro.models import ProUser, WarnMobile, UserSource
from admin.models import User as AdminUser


def sync_account_user(is_all=True):
    """
    同步账号信息
    :return:
    """
    pro_user = ProUser.objects.filter().order_by("-user_create_time").first()
    request_dict = {}
    if pro_user.user_create_time and not is_all:
        request_dict["create_time"] = int(pro_user.user_create_time.timestamp())
    flag = True
    while flag:
        users = inner_server.get_user_all_list(request_dict)
        if users.get("code") == 0:
            objs = []
            for user in users.get("data")["objects"]:
                if not ProUser.objects.filter(user_id=user['user_id']).exists():
                    objs.append(ProUser(
                        user_id=user['user_id'], mobile=user['mobile'],
                        user_create_time=user['create_time'], app_id=user['app_id']
                    ))
            if objs:
                ProUser.objects.bulk_create(objs)
            else:
                flag = False
        else:
            flag = False


@transaction.atomic()
def create_pro_user(mobile, password, is_pro, expire_time, mobile_prefix):
    """
    创建用户
    :param mobile:
    :param password:
    :param is_pro:
    :param expire_time:
    :param mobile_prefix:
    :return:
    """
    if not mobile_prefix == "86":
        user_mobile = mobile_prefix + mobile
    else:
        user_mobile = mobile
    if ProUser.objects.filter(mobile=user_mobile).exists():
        return 16006, "手机号已存在"
    register_dict = dict(
        mobile=user_mobile, username=user_mobile, password=password, app_id=consts.SOURCE_H5, nick=user_mobile
    )
    account = inner_server.register_or_update(register_dict)
    if account.get("code") != 0:
        return account.get("code"), account.get("msg")
    user = account.get("data")
    obj = ProUser(user_id=user['user_id'], mobile=user_mobile, is_pro=is_pro, expire_time=expire_time, re_type="admin",
                  user_create_time=user['create_time'], app_id=consts.SOURCE_H5)
    obj.save()
    WarnMobile(user_id=obj.user_id, mobile=mobile, mobile_prefix=mobile_prefix).save()
    return 0, obj


@transaction.atomic()
def create_admin_user(mobile, remarks="管理员"):
    """
    创建admin用户
    :param mobile:
    :param remarks:
    :return:
    """
    if AdminUser.objects.filter(mobile=mobile).exists():
        return 17002, "账户已经存在"
    password = "pool{}".format(mobile[-4:])
    register_dict = dict(
        mobile=mobile, username=mobile, password=password, app_id=consts.SOURCE_H5, nick=mobile, is_explorer=True
    )
    account = inner_server.register_or_update(register_dict)
    if account.get("code") != 0:
        return account.get("code"), account.get("msg")
    user = account.get("data")
    obj = AdminUser(user_id=user['user_id'], mobile=mobile, user_name=mobile, remarks=remarks)
    obj.save()
    return 0, obj


# def update_admin_user(user_id):
#     """
#     获取admin用户
#     :param user_id:
#     :return:
#     """
#     AdminUser.objects.filter(user_id=user_id)
#     return 0, obj
