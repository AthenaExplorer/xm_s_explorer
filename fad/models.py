from django.db import models


# Create your models here.
class Latitudess(models.Model):
    """
    维度
    """

    name = models.CharField(verbose_name='维度名称', max_length=30)
    identifier = models.CharField(verbose_name='维度名称', max_length=30,unique=True,null=True)
    aParent = models.ForeignKey('self', null=True, on_delete=models.DO_NOTHING)
    ratio = models.FloatField(verbose_name='维度占比', null=True)
    sort_index = models.SmallIntegerField(verbose_name='排序', default=0)
    weighting_factor = models.FloatField(verbose_name='权重系数', null=True)
    is_active = models.BooleanField(verbose_name='是否还在使用', default=1)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='添加日期')

    class Meta:
        ordering = ["sort_index"]


class Scores(models.Model):
    """
    详细数据
    """

    sub_dimension = models.ForeignKey(
        to='latitudess', verbose_name='子维度', on_delete=models.DO_NOTHING
    )
    weighting_factor = models.FloatField(verbose_name='权重系数', null=True)
    ref_data = models.DecimalField(
        verbose_name='参考数据', max_digits=40, decimal_places=4, default=0
    )
    real_time_data = models.DecimalField(
        verbose_name='当日数据', max_digits=40, decimal_places=4, default=0
    )
    basic_scores = models.FloatField(verbose_name='基础得分', null=True)
    weighing_scores = models.FloatField(verbose_name='加权得分', null=True)
    day = models.DateField(auto_now_add=True, verbose_name='记录日期')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='添加日期')
    tag = models.BooleanField(verbose_name='是否为基准', default=0)

    class Meta:
        ordering = ["-day", "-create_time"]


class LatitudeHistory(models.Model):
    lati = models.ForeignKey(
        to='latitudess', verbose_name='维度', on_delete=models.DO_NOTHING
    )
    grade = models.FloatField(verbose_name='维度得分')
    ratio = models.FloatField(verbose_name='维度占比', null=True)
    day = models.DateField(auto_now=True, verbose_name='记录日期')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='添加日期')
    class Meta:
        ordering = ["-day", "-create_time"]


