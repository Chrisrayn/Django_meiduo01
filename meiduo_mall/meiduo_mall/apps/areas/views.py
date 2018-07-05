from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin

# Create your views here.
from areas.models import Areas
from areas.serializers import AreaSerializer, SubAreaSerializer


class AreaViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    """
    获取行政区划信息
    """
    pagination_class = None

    def get_queryset(self):
        # 提供数据集
        if self.action == 'list':
            return Areas.objects.filter(parent=None)
        else:
            return Areas.objects.all()

    def get_serializer_class(self):
        # 提供序列化器
        if self.action == 'list':
            return AreaSerializer
        else:
            return SubAreaSerializer
