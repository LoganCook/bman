from django.db import models
from django.db.models import Sum, Count


class University(models.Model):
    name = models.CharField(max_length=200, blank=False, null=False)

    def __str__(self):
        return self.name


class UniversityD(models.Model):
    name = models.CharField(max_length=200, blank=False, null=False)
    parent = models.ForeignKey(University)

    def __str__(self):
        return self.name


class UniversityDD(models.Model):
    name = models.CharField(max_length=200, blank=False, null=False)
    parent = models.ForeignKey(UniversityD)

    def __str__(self):
        return self.name


class Usage(models.Model):
    """Abstract class of all usage models"""
    start_ts = models.PositiveIntegerField(blank=False, null=False)
    end_ts = models.PositiveIntegerField(blank=False, null=False)
    # levevls classification for aggregating in database
    # Here, they are organisations
    class_one = models.ForeignKey(University, blank=False, null=False)
    class_two = models.ForeignKey(UniversityD, null=True)
    class_three = models.ForeignKey(UniversityDD, null=True)

    class Meta:
        abstract = True

    @classmethod
    def groupby_classifiers(cls, classifiers):
        anns = []
        cn = len(classifiers)
        if cn == 0:
            anns.append('class_one_id')
        elif cn == 1:
            anns.append('class_two_id')
        elif cn == 2:
            anns.append('class_three_id')
        return anns

    @classmethod
    def summarise(cls, start, end, classifiers=[]):
        """
        Base class method which builds a query for derived classes to summarise
        It returns None when failed to find any records at any level
        """
        # when there is no classifier, returns all grouped by class_one_id
        # in other conditions, returns corresponding level filtered by:
        # class_one grouped by class_two_id,
        # class_two grouped by  class_three_id
        # class_three without grouping

        # Derived classes should not process classifiers directly because
        # it is a list which needs special treatment
        if isinstance(classifiers, str):
            classifiers = classifiers.split(';')

        cn = len(classifiers)
        if cn > 3:
            raise ValueError('Number of classifiers exceeded 3')

        try:
            if cn == 0:
                query = cls.objects.all()
            elif cn == 1:
                query = cls.objects.filter(class_one__name=classifiers[0]).all()
            elif cn == 2:
                classifier = UniversityD.objects.filter(parent__name=classifiers[0], name=classifiers[1]).\
                    values_list('id', flat=True)[0]
                query = cls.objects.filter(class_two__id=classifier).all()
            elif cn == 3:
                top_id = UniversityD.objects.filter(parent__name=classifiers[0], name=classifiers[1]).\
                    values_list('id', flat=True)[0]
                classifier = UniversityDD.objects.filter(parent__id=top_id, name=classifiers[2]).\
                    values_list('id', flat=True)[0]
                query = cls.objects.filter(class_three__id=classifier).all()

            if start:
                query = query.filter(start_ts__gte=start)
            if end:
                query = query.filter(end_ts__lte=end)

            anns = cls.groupby_classifiers(classifiers)
            return query, anns
        except IndexError:
            return None


class NovaUsage(Usage):
    # instance's name
    server = models.CharField(max_length=36, blank=False, null=False)
    # instance id in raw snapshot database: aka reporting-unified
    # this can be used when raw data, in terms of states are needed from that database
    instance_id = models.CharField(max_length=36, blank=False, null=False)
    # tenant's openstack_id
    tenant = models.CharField(max_length=36, blank=False, null=False)
    # manager's openstack_id
    account = models.CharField(max_length=36, blank=False, null=False)
    # usage count in seconds
    span = models.PositiveIntegerField(blank=False, null=False)
    # image's openstack_id
    image = models.CharField(max_length=36, blank=False, null=False)
    # flavor's openstack_id
    flavor = models.CharField(max_length=36, blank=False, null=False)
    # name of hypervisor
    hypervisor = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        unique_together = (('instance_id', 'start_ts'), ('instance_id', 'end_ts'))

    @classmethod
    def summarise(cls, start=None, end=None, classifiers=[]):
        query, anns = super().summarise(start, end, classifiers)
        if query is None:
            return NovaUsage.objects.none()

        anns.extend(['tenant', 'server', 'flavor'])

        return query.values(*anns).annotate(span=Sum('span')).all()


class HpcUsage(Usage):
    # hpc username
    owner = models.CharField(max_length=64, blank=False, null=False)
    queue = models.CharField(max_length=64, blank=False, null=False)
    job_id = models.CharField(max_length=64, blank=False, null=False)
    cores = models.PositiveSmallIntegerField(blank=False, null=False)
    cpu_seconds = models.PositiveIntegerField(blank=False, null=False)

    class Meta:
        unique_together = (('job_id', 'start_ts'), ('job_id', 'end_ts'))

    @classmethod
    def summarise(cls, start=None, end=None, classifiers=[]):
        query, anns = super().summarise(start, end, classifiers)
        if query is None:
            return NovaUsage.objects.none()

        anns.append('owner')

        return query.values(*anns).annotate(
            job_count=Count('job_id'),
            cores=Sum('cores'),
            cpu_seconds=Sum('cpu_seconds')).all()
