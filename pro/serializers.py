from rest_framework import serializers
from pro.models import *


class ProUserModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    expire_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    user_create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = ProUser
        fields = ('user_id', 'create_time', "mobile", "expire_time", "is_pro", "invite_code", "user_create_time",
                  "pro_tips_flag")


class CollectibleMinerModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = CollectibleMiner
        fields = '__all__'


class CollectibleWalletAddressModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = CollectibleWalletAddress
        fields = '__all__'


class EachWarnMobileModelSerializer(serializers.ModelSerializer):
    # create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = WarnMobile
        # fields = '__all__'
        exclude = ("create_time", "user_id")


class MinerMonitorModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    warn_mobiles = EachWarnMobileModelSerializer(many=True, read_only=True)

    class Meta:
        model = MinerMonitor
        fields = '__all__'


class EachMinerMonitorModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = MinerMonitor
        # fields = '__all__'
        exclude = ("warn_mobiles",)


class WarnMobileModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    miner_monitors = EachMinerMonitorModelSerializer(many=True, read_only=True)

    class Meta:
        model = WarnMobile
        # fields = '__all__'
        exclude = ("user_id",)


class InviteRecordModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = InviteRecord
        # fields = '__all__'
        exclude = ("user_id",)


class RewardRecordModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = RewardRecord
        fields = '__all__'