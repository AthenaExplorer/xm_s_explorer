from collections import Iterable
from django.http import HttpResponse, JsonResponse

from xm_s_common.decorator import common_ajax_response
from xm_s_common.utils import format_return, generate_date_range
from xm_s_common.page import Page

from explorer.interface import ExplorerBase


@common_ajax_response
def stat_auth_user_for_chart(request):
    return format_return(0)
