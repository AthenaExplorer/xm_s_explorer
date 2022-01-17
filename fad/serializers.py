from rest_framework import serializers

from .models import LatitudeHistory, Latitudess, Scores


class ParentLatitudessSer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'identifier', 'ratio', 'sort_index']
        model = Latitudess


class FactorSer(serializers.ModelSerializer):
    parent_identifier = serializers.ReadOnlyField(source='aParent.identifier')

    class Meta:
        fields = ['id', 'identifier', 'parent_identifier', 'weighting_factor', 'sort_index']
        model = Latitudess


class LatitudessSer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Latitudess


class ScoresSer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='sub_dimension.name')
    parent_identifier = serializers.ReadOnlyField(source='sub_dimension.aParent.identifier')
    identifier = serializers.ReadOnlyField(source='sub_dimension.identifier')

    class Meta:
        exclude = ['id']
        model = Scores


class LatitudeHistorySer(serializers.ModelSerializer):
    identifier = serializers.ReadOnlyField(source='lati.identifier')

    # def to_representation(self, instance):
    #    instance["grade"] = instance.grade*1000
    #    instance= super(self).to_representation(instance)
    def to_representation(self, instance):
        res = super().to_representation(instance=instance)
        res["grade"] = instance.grade*1000
        return res

    class Meta:
        fields = '__all__'
        model = LatitudeHistory
