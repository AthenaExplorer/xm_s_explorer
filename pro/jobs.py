import datetime, time

from pro.models import SendSMS
from xm_s_common.utils import _d, format_fil_to_decimal, format_float_coin, VscodeBase, datetime_to_height
from xm_s_common import inner_server

from xm_s_common.third.binghe_sdk import BingheEsBase


def get_wallet_address_change(wallet_address, balance_value, height):
    """
    查询钱包的具体改变值
    :return:
    """
    # result = BingheEsBase().get_miner_wallet_change(wallet_address, balance_value, start_time)
    # return [data['_source'].get("msg_value") for data in result.get("hits")]
    result = inner_server.get_wallet_address_change({
        "wallet_address": wallet_address, "balance_value": balance_value, "height": height
    })
    balance_values = []
    if result.get("code") == 0:
        balance_values = result.get("data", [])
    return balance_values


def _send_sms(mobile_prefix, mobile, content):
    vscode = VscodeBase(method="explorer")
    if mobile_prefix == "86":
        vscode.send_code(mobile, content)
    else:
        vscode.send_code(mobile_prefix + mobile, content)


def monitor_send_sms(monitor, content):
    content += "【雅典娜浏览器】"
    for warn_mobile in monitor.warn_mobiles.all():
        _send_sms(warn_mobile.mobile_prefix, warn_mobile.mobile, content)
    SendSMS(miner_monitor=monitor, content=content, mobile=warn_mobile.mobile).save()


def send_create_gas_sms(monitor, now_date):
    if monitor.send_sms.filter(create_time__gt=now_date).first():
        return
    actual_value = monitor.miner_value + monitor.overview_pledge
    refer_value = monitor.miner_value_overview + monitor.overview_pledge
    if actual_value > (refer_value * (1 + monitor.value)):
        create_gas_content = "{0}{1}新增算力成本高于参考值{2}%，实际成本：{3} FIL / TiB ，参考值：{4} FIL / TiB"
        content = create_gas_content.format(monitor.miner_no, "（{}）".format(monitor.remarks), int(monitor.value * 100),
                                            round(actual_value, 4), round(refer_value, 4))
        monitor_send_sms(monitor, content)


def send_avg_reward_sms(monitor, now_date):
    if monitor.send_sms.filter(create_time__gt=now_date).first():
        return
    if monitor.miner_value < (monitor.miner_value_overview * (1 - monitor.value)):
        create_gas_content = "{0}{1}产出效率低于参考值{2}%，实际产出效率：{3} FIL / TiB ，参考值：{4} FIL / TiB"
        content = create_gas_content.format(monitor.miner_no, "（{}）".format(monitor.remarks), int(monitor.value * 100),
                                            monitor.miner_value, round(monitor.miner_value_overview, 4))
        monitor_send_sms(monitor, content)


def send_sector_faulty_sms(monitor, now_date):
    """扇区错误提醒"""
    if monitor.send_sms.filter(create_time__gt=now_date).first():
        return
    # 每天发送一次短信。
    if monitor.faulty_sector > 0:
        create_gas_content = "存储供应商ID：{0}存在{1}个错误扇区，请注意继续观察扇区状态"
        content = create_gas_content.format(monitor.miner_no, monitor.faulty_sector)
        monitor_send_sms(monitor, content)


def send_fil_change_sms(monitor, now_date):
    send_sms = monitor.send_sms.first()
    if send_sms:
        now_date = send_sms.create_time
    height = datetime_to_height(now_date)
    balance_values = get_wallet_address_change(monitor.miner_no, monitor.value, height)
    for balance_value in balance_values:
        create_gas_content = "{0}（{1}）有一笔{2} FIL的资金流动，账户余额：{3} FIL"
        content = create_gas_content.format(monitor.miner_no, monitor.wallet_type, format_float_coin(balance_value),
                                            format_float_coin(monitor.balance))
        monitor_send_sms(monitor, content)


def send_fil_balance_sms(monitor, now_date):
    # 当钱包余额监控余额低于设定值,一天只发送一次
    # 当钱包余额监控余额低于设定值的50%后，每小时发送一次短信。
    balance = format_fil_to_decimal(monitor.balance, 4)
    if (balance < monitor.value and not monitor.send_sms.filter(create_time__gt=now_date).first()) \
            or balance < (monitor.value * _d(0.5)):
        create_gas_content = "{0}（{1}）余额不足，账户余额：{2} FIL"
        content = create_gas_content.format(monitor.miner_no, monitor.wallet_type, format_float_coin(monitor.balance))
        monitor_send_sms(monitor, content)
