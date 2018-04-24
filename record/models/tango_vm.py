"""Tango VM configuration and usage"""

import datetime
from django.db import models
from django.db.models import Sum, Avg

from .essentials import Orderline, Usage


class Tangocloudvm(models.Model):
    """Configuration of each vm - do not change once created"""
    # Change configuration, e.g. ram or core will change VM MOID
    orderline = models.ForeignKey(Orderline)
    # VM MOID
    server_id = models.CharField(max_length=100, primary_key=True)
    # name of vm
    server = models.CharField(max_length=100, null=False)
    core = models.SmallIntegerField()
    ram = models.SmallIntegerField()
    os = models.CharField(max_length=100, null=False)
    business_unit = models.CharField(max_length=100, null=False)
    date = models.IntegerField(default=int(datetime.datetime.now().timestamp()))

    def __str__(self):
        return '%s: %s, %d, %d, %s, %s, %d' % (self.server_id, self.server, self.core, self.ram, self.os, self.business_unit, self.date)

    @classmethod
    def get_default_fields(cls):
        return ('server_id', 'server', 'core', 'ram', 'os', 'business_unit')

    @classmethod
    def get(cls, start, end):
        return Tangocloudvm.objects.filter(orderline__tangocloudvmusage__start__gte=start,
                                           orderline__tangocloudvmusage__end__lte=end).all()


class TangocloudvmUsage(Usage):
    storage = models.FloatField()
    span = models.IntegerField()
    uptime_percent = models.FloatField()

    def __str__(self):
        return '%d - %d: span: %d, uptime: %.2f, storage: %.2fG' % (self.start, self.end, self.span, self.uptime_percent, self.storage)

    @classmethod
    def get_default_fields(cls):
        return super().get_default_fields() + ('storage', 'span', 'uptime_percent')

    # @classmethod
    # def create_base_qs(cls, start, end):
    #     return super().create_base_qs(start, end).prefetch_related('tangocloudvm_set')

    # @classmethod
    # def fetch_related(cls, orderline_qs):
    #     def extract_config(orderline):
    #         return orderline.tangocloudvm_set.values(*Tangocloudvm.get_default_fields())[0]

    #     def sum_usage(orderline):
    #         # only span can be summed, others have to be averaged
    #         return orderline.tangocloudvmusage_set.values('orderline_id').annotate(totalSpan=Sum('span'), avgStorage=Avg('storage'), avgUptime=Avg('uptime_percent'))[0]

    #     return super().fetch_related(orderline_qs, sum_usage, extract_config)

    @classmethod
    def get_extract_config_method(cls):
        return lambda orderline: orderline.tangocloudvm_set.values(*Tangocloudvm.get_default_fields())[0]

    @classmethod
    def get_sum_usage_method(cls):
        # only span can be summed, others have to be averaged
        return lambda orderline: orderline.tangocloudvmusage_set.values('orderline_id').\
            annotate(totalSpan=Sum('span'), avgStorage=Avg('storage'), avgUptime=Avg('uptime_percent'))[0]
