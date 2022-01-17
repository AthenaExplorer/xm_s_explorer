from django.db import models


class MinerBase(models.Model):
    """
    矿工算力-基础数据
    """
    miner_no = models.CharField("矿工号", max_length=128)
    total_power_v = models.DecimalField('总算力', max_digits=40, decimal_places=0, default=0)
    avg_reward_v = models.DecimalField('单T奖励', max_digits=8, decimal_places=4, default=0)
    power_increase = models.DecimalField('算力增长', max_digits=40, decimal_places=0, default=0)
    create_gas = models.DecimalField('生产成本', max_digits=40, decimal_places=0, default=0)
    keep_gas = models.DecimalField('维护成本', max_digits=40, decimal_places=0, default=0)
    section_all = models.IntegerField('扇区累计总数', default=0)
    section_fault = models.IntegerField('坏扇区数量', default=0)
    new_sector = models.IntegerField('新增扇区', default=0)
    block_reward = models.DecimalField('单日出块奖励', max_digits=34, decimal_places=0, default=0)
    day = models.DateField('日期', db_index=True)
    join_date = models.DateField("加入时间")
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    objects = models.Manager()

    class Meta:
        ordering = ["-create_time"]


class MinerIndex(models.Model):
    """
    矿工算力-指数,评价指标原始值
    """
    miner_type_choices = ((1, "大矿工"), (2, "小矿工"))  # 区分为总算力大于10PiB
    miner_no = models.CharField("矿工号", max_length=128)
    day = models.DateField('日期', db_index=True)
    # 具体数值
    avg_reward_v = models.DecimalField('单T收益', max_digits=15, decimal_places=10, default=0)
    total_power_v = models.DecimalField('总算力', max_digits=40, decimal_places=0, default=0)
    day_inc_rate_v = models.FloatField(verbose_name="单日算力增长率")
    avg_inc_rate_v = models.FloatField(verbose_name="历史日平均增长率")
    create_gas_week_v = models.DecimalField('七日单T生产成本', max_digits=25, decimal_places=0, default=0)
    keep_gas_week_v = models.DecimalField('七日单T维护成本', max_digits=25, decimal_places=0, default=0)
    section_fault_rate_v = models.DecimalField('七日错误扇区占比', max_digits=15, decimal_places=8, default=0)
    power_increment_7day_v = models.DecimalField('七日算力平均增量', max_digits=40, decimal_places=0, default=0)

    # 指数
    avg_reward_i = models.FloatField('单T收益', null=True)
    total_power_i = models.FloatField('总算力', null=True)
    day_inc_rate_i = models.FloatField(verbose_name="单日算力增长率", null=True)
    avg_inc_rate_i = models.FloatField(verbose_name="历史日平均增长率", null=True)
    create_gas_week_i = models.FloatField('七日单T生产成本', null=True)
    keep_gas_week_i = models.FloatField('七日单T维护成本', null=True)
    section_fault_rate_i = models.FloatField('七日错误扇区占比', null=True)
    power_increment_7day_i = models.FloatField('七日算力平均增量', null=True)
    synthesize_i = models.DecimalField("综合得分", null=True, max_digits=15, decimal_places=10, )
    synthesize_rank = models.IntegerField("综合得分排名", null=True)
    miner_type = models.IntegerField("矿工类型", null=True, choices=miner_type_choices)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    objects = models.Manager()

    class Meta:
        ordering = ["-create_time"]


class CompanyMinerIndex(models.Model):
    """
    矿商算力-指数,评价指标原始值
    """
    miner_type_choices = ((1, "大矿工"), (2, "小矿工"))  # 暂无区分条件
    company_name = models.CharField("矿商名称", max_length=128)
    company_code = models.CharField("矿商编码,这个编码不会改变", max_length=128)
    day = models.DateField('日期', db_index=True)
    # 具体数值
    avg_reward_v = models.DecimalField('单T收益', max_digits=15, decimal_places=10, default=0)
    total_power_v = models.DecimalField('总算力', max_digits=40, decimal_places=0, default=0)
    day_inc_rate_v = models.FloatField(verbose_name="单日算力增长率")
    avg_inc_rate_v = models.FloatField(verbose_name="历史日平均增长率")
    create_gas_week_v = models.DecimalField('七日单T生产成本', max_digits=25, decimal_places=0, default=0)
    keep_gas_week_v = models.DecimalField('七日单T维护成本', max_digits=25, decimal_places=0, default=0)
    section_fault_rate_v = models.DecimalField('七日错误扇区占比', max_digits=15, decimal_places=8, default=0)
    power_increment_7day_v = models.DecimalField('七日算力平均增量', max_digits=40, decimal_places=0, default=0)
    # 指数
    avg_reward_i = models.FloatField('单T收益', null=True)  # 4
    total_power_i = models.FloatField('总算力', null=True)  # 4
    day_inc_rate_i = models.FloatField(verbose_name="单日算力增长率", null=True)  # 无
    avg_inc_rate_i = models.FloatField(verbose_name="历史日平均增长率", null=True)  # 无
    create_gas_week_i = models.FloatField('七日单T生产成本', null=True)  # 无
    keep_gas_week_i = models.FloatField('七日单T维护成本', null=True)  # 2
    section_fault_rate_i = models.FloatField('七日错误扇区占比', null=True)  # 2
    power_increment_7day_i = models.FloatField('七日算力平均增量', null=True)  # 1

    synthesize_i = models.DecimalField("综合得分", null=True, max_digits=15, decimal_places=10, )
    synthesize_rank = models.IntegerField("综合得分排名", null=True)
    miner_type = models.IntegerField("矿工类型", null=True, choices=miner_type_choices, default=1)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    objects = models.Manager()

    class Meta:
        ordering = ["-create_time"]


class CompanyBase(models.Model):
    """
    矿商算力-基础数据
    """
    company_name = models.CharField("矿商名称", max_length=128)
    company_code = models.CharField("矿商编码,这个编码不会改变", max_length=128, null=True)
    total_power_v = models.DecimalField('总算力', max_digits=40, decimal_places=0, default=0)
    avg_reward_v = models.DecimalField('单T奖励', max_digits=12, decimal_places=6, default=0)
    power_increase = models.DecimalField('算力增长', max_digits=40, decimal_places=0, default=0)
    create_gas = models.DecimalField('生产成本', max_digits=40, decimal_places=0, default=0)
    keep_gas = models.DecimalField('维护成本', max_digits=40, decimal_places=0, default=0)
    section_all = models.IntegerField('扇区累计总数', default=0)
    section_fault = models.IntegerField('坏扇区数量', default=0)
    new_sector = models.IntegerField('新增扇区', default=0)
    block_reward = models.DecimalField('单日出块奖励', max_digits=34, decimal_places=0, default=0)
    day = models.DateField('日期', db_index=True)
    join_date = models.DateField("加入时间")
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    objects = models.Manager()

    class Meta:
        ordering = ["-create_time"]
