from rest_framework import serializers
from admin.models import User as AdminUser
from pro.models import *
from master_overview.models import MinerApplyTag


class ProUserModelAdminSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    expire_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    collectible_wallet_address_count = serializers.SerializerMethodField()
    collectible_miner_count = serializers.SerializerMethodField()
    user_create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = ProUser
        fields = ('user_id', 'create_time', "mobile", "expire_time", "is_pro", "invite_code",
                  "re_type", "user_create_time", "app_id", "source", "status", "id",
                  'collectible_wallet_address_count', 'collectible_miner_count')

    def get_collectible_wallet_address_count(self, obj):
        return CollectibleWalletAddress.objects.filter(user_id=obj.user_id).count()

    def get_collectible_miner_count(self, obj):
        return CollectibleMiner.objects.filter(user_id=obj.user_id).count()


class ProUserModelInviteSerializer(serializers.ModelSerializer):
    user_create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    expire_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = ProUser
        fields = ('user_id', "mobile", "is_pro", "invite_code", "invite_count", "user_create_time", "reward_count",
                  "expire_time")


class InviteRecordAdminModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = InviteRecord
        fields = '__all__'


class UserModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = AdminUser
        fields = '__all__'


class UserSourceModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    update_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = UserSource
        fields = '__all__'


class MinerApplyTagModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    update_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = MinerApplyTag
        fields = '__all__'

