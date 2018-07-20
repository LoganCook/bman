"""Tango VM configuration and usage"""

from django.db import models
from django.db.models import Avg

from .essentials import Orderline, Usage


class Storage(models.Model):
    """Configuration of all storage types: HNAS Virtual Volume, HNAS File System, XFS, HCP"""
    orderline = models.ForeignKey(Orderline)
    type = models.CharField(max_length=30)

    def __str__(self):
        return '%s' % self.type

    @classmethod
    def get_default_fields(cls):
        return ('type', )

    @classmethod
    def get(cls, start, end):
        return Storage.objects.filter(orderline__storageusage__start__gte=start,
                                      orderline__storageusage__end__lte=end).all()


class StorageUsage(Usage):
    usage = models.FloatField()

    def __str__(self):
        return '%d - %d: usage: %d' % (self.start, self.end, self.usage)

    @classmethod
    def get_default_fields(cls):
        return super().get_default_fields() + ('usage', )

    @classmethod
    def get_extract_config_method(cls):
        return lambda orderline: orderline.storage_set.values(*Storage.get_default_fields())[0]

    @classmethod
    def get_sum_usage_method(cls):
        return lambda orderline: orderline.storageusage_set.values('orderline_id').\
            annotate(avgUsage=Avg('usage'))[0]
