import json

from rest_framework import serializers

from exponent.models import MinerBase, MinerIndex, CompanyMinerIndex
from xm_s_common.utils import format_fil_to_decimal, format_power, DynamicFieldsModelSerializer


class MinerBaseSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    join_date = serializers.DateField(format='%Y-%m-%d')

    def to_representation(self, instance):
        result_dict = super().to_representation(instance)
        result_dict['create_gas'] = format_fil_to_decimal(result_dict['create_gas'], 0)
        result_dict['keep_gas'] = format_fil_to_decimal(result_dict['keep_gas'], 0)
        result_dict['total_power_v'] = format_power(result_dict['total_power_v'])
        return result_dict

    class Meta:
        model = MinerBase
        fields = "__all__"
        # exclude = ("user_id",)
        # read_only_fields = ("user_id",)


class MinerIndexSerializer(DynamicFieldsModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    def to_representation(self, instance):
        result_dict = super().to_representation(instance)
        result_dict['create_gas_week_v'] = format_fil_to_decimal(result_dict['create_gas_week_v'], 6)
        result_dict['keep_gas_week_v'] = format_fil_to_decimal(result_dict['keep_gas_week_v'], 6)
        result_dict['total_power_v'] = format_power(result_dict['total_power_v'])
        return result_dict

    class Meta:
        model = MinerIndex
        fields = "__all__"
        # exclude = ("user_id",)
        # read_only_fields = ("user_id",)


class MinerIndexRankSerializer(DynamicFieldsModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    def to_representation(self, instance):
        result_dict = super().to_representation(instance)
        company = self.context.get("company").get(result_dict.get('miner_no'))
        result_dict['company'] = company.get("name") if company else None

        if result_dict.get('create_gas_week_v'):
            result_dict['create_gas_week_v'] = format_fil_to_decimal(result_dict['create_gas_week_v'], 6)
        if result_dict.get('keep_gas_week_v'):
            result_dict['keep_gas_week_v'] = format_fil_to_decimal(result_dict['keep_gas_week_v'], 6)
        if result_dict.get('total_power_v'):
            result_dict['total_power_v'] = format_power(result_dict['total_power_v'])
        return result_dict

    class Meta:
        model = MinerIndex
        fields = "__all__"
        # exclude = ("user_id",)
        # read_only_fields = ("user_id",)


class MinerIndexLineSerializer(serializers.ModelSerializer):
    """
    仅综合序列化指数
    """

    class Meta:
        model = MinerIndex
        fields = ("synthesize_i", "day", "miner_no")
        # exclude = ("user_id",)
        # read_only_fields = ("user_id",)


class CompanyIndexLineSerializer(serializers.ModelSerializer):
    """
    仅综合序列化指数
    """

    class Meta:
        model = CompanyMinerIndex
        fields = ("synthesize_i", "day", "company_name")
        # exclude = ("user_id",)
        # read_only_fields = ("user_id",)


class CompanyMinerIndexSerializer(DynamicFieldsModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    def to_representation(self, instance):
        result_dict = super().to_representation(instance)
        if result_dict.get('create_gas_week_v'):
            result_dict['create_gas_week_v'] = format_fil_to_decimal(result_dict['create_gas_week_v'], 6)
        # result_dict['avg_reward_v'] = 1
        if result_dict.get('keep_gas_week_v'):
            result_dict['keep_gas_week_v'] = format_fil_to_decimal(result_dict['keep_gas_week_v'], 6)
        if result_dict.get('total_power_v'):
            result_dict['total_power_v'] = format_power(result_dict['total_power_v'])
        return result_dict

    class Meta:
        model = CompanyMinerIndex
        fields = "__all__"
        # exclude = ("user_id",)
        # read_only_fields = ("user_id",)
