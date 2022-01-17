from rest_framework import serializers

from master_overview.models import MinerTag, MinerApplyTag


class MinerTagSerializer(serializers.ModelSerializer):
    # create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    class Meta:
        model = MinerTag
        # fields = "__all__"
        exclude = ("create_time", "id")


class MinerApplyTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinerApplyTag
        exclude = ("id",)


class MinerTagQuerySerializer(serializers.Serializer):
    miner_no_list = serializers.ListField(child=serializers.CharField(max_length=128), required=False)


class MinerApplyTagSetSerializer(serializers.Serializer):
    miner_no = serializers.CharField(max_length=32)
    address = serializers.CharField(max_length=128)
    cn_tag = serializers.CharField(max_length=32, required=False)
    en_tag = serializers.CharField(max_length=32)
    contact = serializers.CharField(max_length=200)
    sign_bytes = serializers.CharField()
