from rest_framework import serializers

from areas.models import Areas


class AreaSerializer(serializers.ModelSerializer):
    """
    行政区化信息序列化器
    """

    class Meta:
        model = Areas
        fields = ('id', 'name')


class SubAreaSerializer(serializers.ModelSerializer):
    """
    子级行政区化信息序列化器
    """
    subs = AreaSerializer(many=True, read_only=True)

    class Meta:
        model = Areas
        fields = ('id', 'name', 'subs')
