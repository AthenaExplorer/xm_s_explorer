from django.db import models


class User(models.Model):
    user_id = models.CharField('用户id', max_length=32, db_index=True)
    user_name = models.CharField('账号', max_length=32, db_index=True, null=True)
    mobile = models.CharField('手机号', max_length=20, db_index=True, null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    remarks = models.CharField('备注', max_length=128, db_index=True)

    class Meta:
        ordering = ["-create_time"]


class TagStatus(models.Model):
    status = models.BooleanField('状态', max_length=20, default=False)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ["-create_time"]
