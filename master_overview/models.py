from django.db import models


# Create your models here.

class MinerTag(models.Model):
    miner_no = models.CharField("矿工号", max_length=32)
    tag = models.CharField("标签名称", max_length=64)
    signed = models.BooleanField("是否认证", default=False)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    objects = models.Manager()

    class Meta:
        ordering = ["-create_time"]


class MinerApplyTag(models.Model):
    miner_no = models.CharField("矿工号", max_length=32)
    address = models.CharField('钱包地址', max_length=128, null=True)
    cn_tag = models.CharField("标签名称", max_length=64, null=True)
    en_tag = models.CharField("标签名称", max_length=64)
    contact = models.CharField("联系方式", max_length=256, null=True)
    signed = models.BooleanField("是否认证", default=False)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)
    status = models.BooleanField('状态', default=True)

    class Meta:
        ordering = ["-create_time"]
