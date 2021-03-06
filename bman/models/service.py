from django.db import models

from .person import Role, Account


def extract_fields(source, fields):
    """Generate dictionary with specified fields from a dictionary."""
    output = {}
    for name in fields:
        if name in source:
            output[name] = source[name]
    return output


class Catalog(models.Model):
    """For AccessServices and other simple services"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    site = models.URLField('URL of service', blank=True, default='')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# from django.contrib.contenttypes.fields import GenericForeignKey
# from django.contrib.contenttypes.models import ContentType
# class Service(models.Model):
    # name = models.CharField(max_length=100)
    # service_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # service_id = models.PositiveIntegerField()
    # content_object = GenericForeignKey('service_type', 'service_id')
    # contractor = models.ForeignKey(Role)
    # start_date = models.DateField(blank=True, null=True)
    # end_date = models.DateField(blank=True, null=True)
#
    # def __str__(self):
        # return "%s (%s) managed by %s" % (self.name, self.catalog, self.contractor)

class BasicService(models.Model):
    STATUS = (
        ('E', 'enabled'),
        ('S', 'suspended'),
        ('D', 'ended'),
    )
    # Might be a one-to-one, at least spreadsheet only allows one
    contractor = models.ForeignKey(Role)  # Manager of a service
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(help_text='Service status', max_length=1, choices=STATUS, default='E')

    class Meta:
        abstract = True

    @property
    def descriptive_name(self):
        # May change to another property: summary, or long_name, verbose_name. Cannot use name
        raise NotImplementedError()

    @property
    def service_url_name(self):
        """Used for building reverse url under /object/ when it is not the main object"""
        return self.__class__.__name__

    @property
    def billing_organisation(self):
        # role and account has one-to-one relationship
        try:
            return self.contractor.account.billing_org
        except Account.DoesNotExist:
            return self.contractor.organisation

    def to_dict(self):
        """Convert all necessary related objects into a dict for clients
        """
        billing_org = self.billing_organisation
        return {
            'billing_id': billing_org.id,  # billing organisation id
            'billing': billing_org.name,   # billing organisation name
            'organisation_id': self.contractor.organisation.id,
            'organisation': self.contractor.organisation.name,
            'contractor_id': self.contractor.id,
            'contractor': self.contractor.person.full_name,
            'email': self.contractor.email
        }


class AccessService(BasicService):
    """Services only need a name"""
    catalog = models.ForeignKey(Catalog)

    def __str__(self):
        return "%s has access to %s" % (self.contractor.person, self.catalog)

    def descriptive_name(self):
        return self.catalog.name


class RDS(BasicService):
    allocation_num = models.CharField('Allocation number', max_length=100)
    filesystem = models.CharField(max_length=100, blank=True, default='')
    approved_size = models.PositiveIntegerField(help_text='In GB', default=0)
    collection_name = models.CharField(max_length=200)

    def __str__(self):
        return "%s manages %s" % (self.contractor.person, self.allocation_num)

    def descriptive_name(self):
        return 'RDS'

    def to_dict(self):
        """Convert all necessary related objects into a dict for clients
        """
        base_info = super().to_dict()
        fields = ["allocation_num", "filesystem", "approved_size", "collection_name"]
        base_info.update(extract_fields(self.__dict__, fields))
        return base_info


class Nectar(BasicService):
    """Provide tracking to Nectar projects
    One project for billing purpose only allow to have one contractor.
    """
    tenant = models.CharField(help_text='Nectar project name', max_length=100, blank=True, default='')
    openstack_id = models.CharField(max_length=36, unique=True)
    description = models.TextField(blank=True, default='')
    allocation_id = models.PositiveIntegerField(null=True)

    def __str__(self):
        return "%s (%s) is bound to %s" % (self.tenant, self.openstack_id, self.contractor.person)

    def descriptive_name(self):
        return 'Nectar'

    def to_dict(self):
        """Convert all necessary related objects into a dict for clients
        """
        base_info = super().to_dict()
        base_info.update(
            openstack_id=self.openstack_id,
            tenant=self.tenant)
        return base_info
