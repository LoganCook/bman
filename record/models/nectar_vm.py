"""Tango VM configuration and usage"""

import datetime
from django.db import models
from django.db.models import Sum

from .essentials import Orderline, Usage


class Nectarvm(models.Model):
    """Configuration of each vm - do not change once created"""
    orderline = models.ForeignKey(Orderline)
    # name of vm
    server = models.CharField(max_length=100, null=False)
    # # UUID of server
    # server_id = models.CharField(max_length=36, unique=True)
    hypervisor = models.CharField(max_length=100)
    # flavor name: m1.xlarge
    flavor = models.CharField(max_length=20)
    # from flavor, we get vcpus, ram and other configuration values
    vcpus = models.SmallIntegerField()
    ram = models.SmallIntegerField()
    disk = models.SmallIntegerField()
    ephemeral = models.SmallIntegerField()
    date = models.IntegerField(default=int(datetime.datetime.now().timestamp()))

    def __str__(self):
        return '%s: %d, %d, %d, %d, %d' % (self.server, self.vcpus, self.ram, self.disk, self.ephemeral, self.date)

    @classmethod
    def get_default_fields(cls):
        # some fields are not on the default list
        return ('server', 'vcpus', 'ram', 'disk', 'ephemeral')

    @classmethod
    def get(cls, start, end):
        return cls.objects.filter(orderline__nectarvmusage__start__gte=start,
                                  orderline__nectarvmusage__end__lte=end).all()


class NectarvmUsage(Usage):
    span = models.IntegerField()

    def __str__(self):
        return '%d - %d: span: %d' % (self.start, self.end, self.span)

    @classmethod
    def get_default_fields(cls):
        return super().get_default_fields() + ('span', )

    # @classmethod
    # def create_base_qs(cls, start, end):
    #     return super().create_base_qs(start, end).prefetch_related('nectarvm_set')

    # @classmethod
    # def fetch_related(cls, orderline_qs):
    #     def extract_config(orderline):
    #         return orderline.nectarvm_set.values(*Nectarvm.get_default_fields())[0]

    #     def sum_usage(orderline):
    #         # only span can be summed, others have to be averaged
    #         return orderline.nectarvmusage_set.values('orderline_id').annotate(totalSpan=Sum('span'))[0]

    #     return super().fetch_related(orderline_qs, sum_usage, extract_config)

    @classmethod
    def get_extract_config_method(cls):
        return lambda orderline: orderline.nectarvm_set.values(*Nectarvm.get_default_fields())[0]

    @classmethod
    def get_sum_usage_method(cls):
        # only span can be summed
        return lambda orderline: orderline.nectarvmusage_set.values('orderline_id').\
            annotate(totalSpan=Sum('span'))[0]
