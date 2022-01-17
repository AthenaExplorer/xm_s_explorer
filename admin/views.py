import json

import datetime
from django.db.models import Q, Sum
from django.utils import timezone
from xm_s_common.decorator import common_ajax_response
from xm_s_common.utils import format_return
from admin.models import User, TagStatus
from admin import interface
from pro.models import ProUser, InviteRecord, UserSource
from master_overview.models import MinerApplyTag
from xm_s_common.page import Page
from admin.serializers import ProUserModelAdminSerializer, ProUserModelInviteSerializer, \
    InviteRecordAdminModelSerializer, UserModelSerializer, UserSourceModelSerializer, MinerApplyTagModelSerializer
from pro.prefix import MOBILE_PREFIX


def check_admin_user(func):
    def _decorator(request, *args, **kwargs):
        #  request.user_id = "b88c7ca4d7f711ebac9b0242ac160035"
        if not request.user_id:
            return format_return(99905)
        if not User.objects.filter(user_id=request.user_id).exists():
            return format_return(17001)
        return func(request, *args, **kwargs)
    return _decorator


@common_ajax_response
@check_admin_user
def get_pro_user_list(request):
    interface.sync_account_user(is_all=False)
    is_pro = request.POST.get("is_pro")
    status = request.POST.get("status")
    user_create_time_start = request.POST.get("create_time_start")
    user_create_time_end = request.POST.get("create_time_end")
    mobile = request.POST.get("mobile")
    app_id = request.POST.get("app_id")
    re_type = request.POST.get("re_type")
    source = request.POST.get("source")
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    request_dict = {}
    for key_words in ["status", "mobile", "app_id", "re_type"]:
        if request.POST.get(key_words):
            request_dict[key_words] = request.POST.get(key_words)
    if user_create_time_start:
        request_dict["user_create_time__gte"] = user_create_time_start
    if user_create_time_end:
        request_dict["user_create_time__lte"] = user_create_time_end
    if source:
        request_dict["source__contains"] = source
    objs = ProUser.objects.filter(**request_dict)
    now = datetime.datetime.now()
    if is_pro == "1":
        objs = objs.filter(Q(is_pro=True, expire_time__isnull=True) | Q(is_pro=True, expire_time__gte=now))
    if is_pro == "0":
        objs = objs.filter(Q(is_pro=False) | Q(is_pro=True, expire_time__lt=now))
    objs = objs.order_by("-user_create_time")
    if page_index:
        data_result = Page(objs, page_size).page(page_index)
        data_result["objects"] = ProUserModelAdminSerializer(data_result["objects"], many=True).data
    else:
        data_result = ProUserModelAdminSerializer(objs, many=True).data
    return format_return(0, data=data_result)


@common_ajax_response
@check_admin_user
def add_pro_user(request):
    mobile = request.POST.get('mobile')
    password = request.POST.get('password')
    is_pro = request.POST.get('is_pro', 0)
    expire_time = request.POST.get('expire_time')
    mobile_prefix = request.POST.get('mobile_prefix', '86')
    if not mobile.isdigit():
        return format_return(16001, data=None, msg='无效的手机号')
    if mobile_prefix not in [i['prefix'] for i in MOBILE_PREFIX]:
        return format_return(16005, "手机区号错误")
    if expire_time:
        expire_time = datetime.datetime.strptime(expire_time, '%Y-%m-%d %H:%M:%S')
    else:
        expire_time = None
    code, result = interface.create_pro_user(mobile, password, is_pro, expire_time, mobile_prefix)
    if code == 0:
        data = ProUserModelAdminSerializer(result).data
        return format_return(0, data=data)
    return format_return(code, msg=result)


@common_ajax_response
@check_admin_user
def update_pro_user(request):
    """
    编辑用户
    :param request:
    :return:
    """
    oid = int(request.POST.get('id'))
    obj = ProUser.objects.filter(id=oid).first()
    is_pro = request.POST.get('is_pro')
    expire_time = request.POST.get('expire_time')
    status = request.POST.get('status')
    if not obj:
        return format_return(16004, msg='无效的ID')
    if expire_time:
        obj.expire_time = timezone.datetime.strptime(expire_time, '%Y-%m-%d %H:%M:%S')
    else:
        obj.expire_time = None
    if status is not None:
        obj.status = status
    if is_pro is not None:
        obj.is_pro = is_pro
    obj.save()
    data = ProUserModelAdminSerializer(obj).data
    return format_return(0, data=data)


@common_ajax_response
@check_admin_user
def get_invite_user_list(request):
    """
    注册邀请列表
    :param request:
    :return:
    """
    mobile = request.POST.get("mobile")
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    request_dict = {"invite_code__isnull": False}
    if mobile:
        request_dict["mobile"] = mobile
    objs = ProUser.objects.filter(**request_dict).order_by("-invite_count")
    if page_index:
        data_result = Page(objs, page_size).page(page_index)
        data_result["objects"] = ProUserModelInviteSerializer(data_result["objects"], many=True).data
    else:
        data_result = ProUserModelInviteSerializer(objs, many=True).data
    return format_return(0, data=data_result)


@common_ajax_response
@check_admin_user
def get_invite_info_list(request):
    """
    注册邀请详细列表
    :param request:
    :return:
    """
    invite_code = request.POST.get("invite_code")
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    objs = InviteRecord.objects.filter(invite_code=invite_code)
    data_result = Page(objs, page_size).page(page_index)
    data_result["objects"] = InviteRecordAdminModelSerializer(data_result["objects"], many=True).data
    return format_return(0, data=data_result)


@common_ajax_response
@check_admin_user
def get_admin_user_info(request):
    user_id = request.user_id
    user = User.objects.filter(user_id=user_id).first()
    data = UserModelSerializer(user).data
    return format_return(0, data=data)


@common_ajax_response
@check_admin_user
def create_admin_user(request):
    mobile = request.POST.get('mobile')
    remarks = request.POST.get('remarks')
    if not mobile.isdigit():
        return format_return(16001, data=None, msg='无效的手机号')
    code, result = interface.create_admin_user(mobile, remarks)
    if code == 0:
        data = UserModelSerializer(result).data
        return format_return(0, data=data)
    return format_return(code, msg=result)


@common_ajax_response
@check_admin_user
def get_admin_user_list(request):
    user_id_list = json.loads(request.POST.get('user_id_list', '[]'))
    if user_id_list:
        user_list = User.objects.filter(user_id__in=user_id_list)
    else:
        user_list = User.objects.filter()
    data = UserModelSerializer(user_list, many=True).data
    return format_return(0, data=data)


@common_ajax_response
@check_admin_user
def get_user_source_list(request):
    page_index = int(request.POST.get('page_index', 0))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    objs = UserSource.objects.filter()
    if page_index:
        data_result = Page(objs, page_size).page(page_index)
        data_result["objects"] = UserSourceModelSerializer(data_result["objects"], many=True).data
    else:
        data_result = {"objects": UserSourceModelSerializer(objs, many=True).data}
    return format_return(0, data=data_result)


@common_ajax_response
@check_admin_user
def create_user_source(request):
    code = request.POST.get('code')
    title = request.POST.get('title')
    is_source = UserSource.objects.filter(code=code).exists()
    if is_source:
        return format_return(17003)
    source = UserSource(code=code, title=title)
    source.save()
    return format_return(0, data=UserSourceModelSerializer(source).data)


@common_ajax_response
@check_admin_user
def update_user_source(request):
    """
    编辑用户
    :param request:
    :return:
    """
    oid = int(request.POST.get('id'))
    title = request.POST.get('title')
    source = UserSource.objects.filter(id=oid).first()
    if not source:
        return format_return(16004, msg='无效的ID')
    if title is not None:
        source.title = title
    source.save()
    data = UserSourceModelSerializer(source).data
    return format_return(0, data=data)


@common_ajax_response
@check_admin_user
def get_miner_apply_tag_list(request):
    status = request.POST.get("status")
    keywords = request.POST.get("keywords")
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    query = MinerApplyTag.objects.filter()
    if status:
        query = query.filter(status=status)
    if keywords:
        query = query.filter(Q(miner_no__contains=keywords) | Q(address__contains=keywords))
    data_result = Page(query, page_size).page(page_index)
    data_result["objects"] = MinerApplyTagModelSerializer(data_result["objects"], many=True).data
    return format_return(0, data=data_result)


@common_ajax_response
@check_admin_user
def update_miner_apply_tag(request):
    oid = int(request.POST.get('id'))
    status = request.POST.get("status")
    tag = MinerApplyTag.objects.filter(id=oid).first()
    if not tag:
        return format_return(16004, msg='无效的ID')
    if status is not None:
        tag.status = status
    tag.save()
    data = MinerApplyTagModelSerializer(tag).data
    return format_return(0, data=data)


@common_ajax_response
@check_admin_user
def update_tag_status(request):
    status = int(request.POST.get("status"))
    tag_status = TagStatus.objects.filter().first()
    if tag_status:
        tag_status.status = status
    else:
        tag_status = TagStatus(status=status)
    tag_status.save()
    return format_return(0, data=status)
