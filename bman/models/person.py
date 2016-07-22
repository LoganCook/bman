from django.db import models

from django.core import validators

from .organisation import Organisation
from .relationship import RelationshipType, Relationship
from .utils import get_related

class Person(models.Model):
    TITLE = (('Dr', 'Dr'), ('APro', 'Associate Professor'), ('Prof', 'Professor'),
             ('Mr', 'Mr'), ('Mrs', 'Mrs'), ('Ms', 'Ms'))
    first_name = models.CharField('first name', max_length=30)
    last_name = models.CharField('last name', max_length=30)
    insightly_id = models.PositiveIntegerField(blank=True, null=True)
    title = models.CharField(max_length=4, choices=TITLE, blank=True, default='')
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        if self.title:
            return "%s %s %s" % (self.title, self.first_name, self.last_name)
        else:
            return "%s %s" % (self.first_name, self.last_name)

    @property
    def full_name(self):
        """Returns the person's full name."""
        return '%s %s' % (self.first_name, self.last_name)

    def get_all_services(self):
        """All services this Person linked to"""
        services = []
        roles = self.role_set.all()
        for role in roles:
            services.extend(role.get_all_services())
        return services

    def get_service(self, name=None):
        """All services this Person linked to"""
        if name is None:
            return []

        services = []
        roles = self.role_set.all()
        for role in roles:
            result = role.get_service(name=name)
            if result:
                services.append(result)
        return services


# This is a non-direct expanded relationship: Organisation - Person
# When a natural Person appears in an organisation
# with a role, relationships can be established:
# A staff member - in an org, has a relationship
# Is a student - in an org, has a relationship with it
class Role(models.Model):
    person = models.ForeignKey(Person)
    organisation = models.ForeignKey(Organisation)
    relationshiptype = models.ForeignKey(RelationshipType) #Must be one of Organisation-Person type
    description = models.TextField(blank=True, default='')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    email = models.EmailField('email address')
    phone = models.CharField(max_length=30, blank=True, default='')
    mobile = models.CharField(max_length=30, blank=True, default='')

    class Meta:
        ordering = ['relationshiptype']

    def __str__(self):
        """Role description read from Orgainsation to Person"""
        return "%s %s %s" % (self.organisation, self.relationshiptype.forward, self.person)

    @property
    def backward(self):
        """Role description read from Person to Orgainsation"""
        return "%s %s %s" % (self.person, self.relationshiptype.backward, self.organisation)

    def get_all_services(self):
        """All services this role linked to"""
        services = []
        #better to auto-discover services from which to query
        services.extend(self.accessservice_set.all())
        services.extend(self.rds_set.all())
        services.extend(self.nectar_set.all())
        return services

    def get_service(self, name=None):
        """Get a service of a role linked to

           param service: name of a service, has to be name of one of classess in service.py
        """
        if name is None:
            return None

        service = name.lower() + '_set'
        if hasattr(self, service):
            return getattr(self, service).first()
        else:
            return None

    def get_students(self):
        #Only empolyee can be a supervisor
        students = []
        if self.relationshiptype.name == 'Employment':
            sup_type = RelationshipType.objects.get(name='Supervision')
            student_rels = Relationship.objects.filter(relationshiptype=sup_type, tail_id=self.pk)
            students = [ Role.objects.get(pk=rel.head_id).person for rel in student_rels ]
        return students

    def get_supervisors(self):
        #Only student can have supervisors
        supervisors = []
        if self.relationshiptype.name == 'Study':
            sup_type = RelationshipType.objects.get(name='Supervision')
            supervisor_rels = Relationship.objects.filter(relationshiptype=sup_type, head_id=self.pk)
            supervisors = [ Role.objects.get(pk=rel.tail_id).person for rel in supervisor_rels ]
        return supervisors


class Account(models.Model):
    """Billing account of a role

       One role has one account
    """
    STATUS = (
        ('A', 'active'),
        ('T', 'terminated'),
    )
    role = models.OneToOneField(Role)
    username = models.CharField(max_length=30,
        help_text='Required. 30 characters or fewer. Letters, digits and . _ only.',
        validators=[
            validators.RegexValidator(r'^[\w.]+$',
                                      'Enter a valid username. This value may contain only letters, numbers and /./_ characters.',
                                      'invalid'),
        ])
    status = models.CharField(max_length=1, choices=STATUS, default='A')
    #for certain service? catalog = models.ForeignKey(Catalog)
    billing_org = models.ForeignKey(Organisation, blank=True, null=True)

    def __str__(self):
        return "%s belongs to %s" % (self.username, self.role.person)
