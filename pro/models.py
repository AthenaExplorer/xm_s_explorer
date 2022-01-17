from django.db import models


class ProUser(models.Model):
    re_types = (
        ('register', '用户注册'),
        ('admin', '后台添加')
    )
    user_id = models.CharField('用户id', max_length=32, db_index=True, unique=True)
    mobile = models.CharField('手机号', max_length=20, db_index=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    expire_time = models.DateTimeField('到期时间', null=True)
    is_pro = models.BooleanField('是否是Pro', default=False)
    # 1:如果is_pro是False 普通用户 2：如果is_pro是True 并且 expire_time None 永久 3：如果is_pro是True 并且 expire_time 有值 在判断是否过期
    status = models.BooleanField('状态', default=True)
    re_type = models.CharField('注册方法', max_length=32, choices=re_types, default="register")
    user_create_time = models.DateTimeField('用户注册时间', null=True)
    app_id = models.CharField('内部app_id', max_length=64, null=True, db_index=True)
    invite_code = models.CharField('邀请码', max_length=16, unique=True, null=True)
    invite_count = models.IntegerField('邀请码人数',  db_index=True, default=0)
    reward_count = models.IntegerField('奖励月份', db_index=True, default=0)
    pro_tips_flag = models.BooleanField('赠送pro的提醒标记', default=False)
    source = models.CharField('来源', max_length=16, null=True)

    class Meta:
        ordering = ["-create_time"]


class WarnMobile(models.Model):
    """提醒手机号"""
    mobile = models.CharField(max_length=11)
    mobile_prefix = models.CharField(max_length=4, default='86')
    user_id = models.CharField('用户id', max_length=32, db_index=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)


class CollectibleMiner(models.Model):
    """节点收藏"""
    user_id = models.CharField('用户id', max_length=32, db_index=True)
    miner_no = models.CharField('节点id', max_length=32)
    remarks = models.CharField('备注', max_length=128, null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        unique_together = [
            ("user_id", "miner_no")
        ]
        ordering = ["-create_time"]


class CollectibleWalletAddress(models.Model):
    """钱包收藏"""
    user_id = models.CharField('用户id', max_length=32, db_index=True)
    wallet_address = models.CharField('钱包地址', max_length=128)
    remarks = models.CharField('备注', max_length=128, null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        unique_together = [
            ("user_id", "wallet_address")
        ]
        ordering = ["-create_time"]


class MinerMonitor(models.Model):
    """节点监控"""
    warn_methods = (
        ('create_gas', '算力成本'),
        ('avg_reward', '产出效率'),
        ('fil_change', '资金变动'),
        ('fil_balance', '资金余额'),
        ('sector_faulty', '扇区错误')
    )
    user_id = models.CharField('用户id', max_length=32, db_index=True)
    miner_no = models.CharField('节点id', max_length=128)
    sector_size = models.CharField('扇区大小', max_length=32, null=True)
    balance = models.DecimalField('钱包余额', max_digits=34, decimal_places=0, default=0)
    wallet_type = models.CharField('钱包类型', max_length=32, null=True)
    overview_pledge = models.DecimalField('全网质押 FIL/TiB', max_digits=10, decimal_places=4, default=0)
    miner_value_overview = models.DecimalField('全网24成本or产出 FIL/TiB', max_digits=10, decimal_places=4, default=0)
    miner_value = models.DecimalField('24成本or产出 FIL/TiB', max_digits=10, decimal_places=4, default=0)
    remarks = models.CharField('备注', max_length=128, null=True)
    value = models.DecimalField('阀值', max_digits=34, decimal_places=4, default=0)
    warn_method = models.CharField('警告方法', max_length=32, choices=warn_methods)
    warn_mobiles = models.ManyToManyField(WarnMobile, related_name="miner_monitors", help_text='通信手机号')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    total_sector = models.IntegerField('总的扇区数', default=0)
    active_sector = models.IntegerField('有效的扇区数', default=0)
    faulty_sector = models.IntegerField('错误的扇区数', default=0)
    recovering_sector = models.IntegerField('恢复中的扇区数', default=0)

    class Meta:
        unique_together = [
            ("user_id", "miner_no", "warn_method")
        ]
        ordering = ['-create_time']


class SendSMS(models.Model):
    """监控短信发送记录"""
    # db_constraint
    miner_monitor = models.ForeignKey(MinerMonitor, help_text='监控ID', related_name='send_sms', null=True,
                                      on_delete=models.CASCADE)
    content = models.CharField(max_length=256, null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    mobile = models.CharField(max_length=32, null=True)

    class Meta:
        ordering = ["-create_time"]


# 运营活动相关
class InviteRecord(models.Model):
    """邀请记录"""
    invite_code = models.CharField('邀请码', max_length=16, null=True)
    user_id = models.CharField('被邀请人用户id', max_length=32, db_index=True)
    mobile = models.CharField('被邀请人手机号', max_length=20, db_index=True)
    status = models.BooleanField('被邀请人状态', default=False)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ["-create_time"]


class RewardRecord(models.Model):
    """奖励记录"""
    invite_code = models.CharField('邀请码', max_length=16, null=True)
    reward = models.IntegerField('奖励')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ["-create_time"]


class UserSource(models.Model):
    """用户来源"""
    code = models.CharField('来源码', max_length=16, unique=True)
    title = models.CharField('名称', max_length=32, null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ["-create_time"]