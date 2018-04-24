"""HPC configurations and usages"""

from django.db import models
from django.db.models import Sum, FloatField
from django.db.models.functions import Cast

from .essentials import Usage


# This table has data from Tizard and Tango compute
class HpcUsage(Usage):
    """Statistics of HPC jobs"""
    partition = models.CharField(max_length=20)
    cpu_seconds = models.IntegerField()
    count = models.IntegerField()

    def __str__(self):
        return '%d - %d: %d jobs run for total %d seconds' % (self.start, self.end, self.count, self.cpu_seconds)

    @classmethod
    def get_default_fields(cls):
        return super().get_default_fields() + ('partition', 'cpu_seconds', 'count')

    @classmethod
    def get_sum_usage_method(cls):
        return lambda orderline: orderline.hpcusage_set.values('orderline_id').\
            annotate(totalCPUHours=Cast(Sum('cpu_seconds'), FloatField()) / 3600, totalCount=Sum('count'))[0]
