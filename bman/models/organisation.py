from django.db import models


def get_parent_ids_of(bottom_id, rtype=None):
    """Get parent entity id(tail id)s of a Relationship type of a model instance with bottom_id

    In such tree structure, it gets tail_id of such RelationshipType recursively.
    The return is a list in the order of bottom_id to the top:
    [parent_id, grand_id, great_grand_id, ...]

    rtype can be a string or a RelationshipType instance. By default, it finds child
    Organisations of an Organisation defined by RelationshipType.name='Organisation'.
    """
    from .relationship import RelationshipType, Relationship
    if rtype is None:
        rtype = RelationshipType.objects.get(name='Organisation')
    elif isinstance(rtype, str):
        rtype = RelationshipType.objects.get(name=rtype)

    # With tree structure, every entity has only one parent
    parent_ids = []

    parents = Relationship.objects.filter(relationshiptype=rtype, head_id=bottom_id)
    if parents:
        for parent in parents:
            parent_ids.append(parent.tail_id)
            level_up = get_parent_ids_of(parent.tail_id, rtype)
            if level_up:
                parent_ids.extend(level_up)

    return parent_ids


def get_child_ids_of(top_id, rtype=None):
    """Get ids of entities of Relationships of a model instance with top_id is the
       tail_id of such RelationshipType recursively. The return is a dictionary of
       recursive fashion like this:
    {
      "68": {},
      "78": {
        "134": {}
      },
      "127": {}
    }
    rtype can be a string or a RelationshipType instance. By default, it finds child
    Organisations of an Organisation defined by RelationshipType.name='Organisation'.
    """
    from .relationship import RelationshipType, Relationship
    if rtype is None:
        rtype = RelationshipType.objects.get(name='Organisation')
    elif isinstance(rtype, str):
        rtype = RelationshipType.objects.get(name=rtype)

    children = Relationship.objects.filter(relationshiptype=rtype, tail_id=top_id)
    child_ids = {}
    for child in children:
        child_ids[str(child.head_id)] = get_child_ids_of(child.head_id, rtype)
    return child_ids

def flat_ids(ids, flattened):
    """Flat ids in a recusive dictionary and return a list

    Remember to provide the initial flattened with [].
    """
    for child in ids:
        flattened.append(child)
        if ids[child]:
            flat_ids(ids[child], flattened)
    return flattened

def get_tree_leaves(ids, query_model):
    """Get names of ids of a Model in a dictionary of recursive fashion for display
    {
      "68": {
        "name": "Mind and Brain"
      },
      "78": {
        "name": "Infection and Immunology",
        "children": {
          "134": {
            "name": "David Lynn, SAHMRI"
          }
        }
      },
      "127": {
        "name": "SAHMRI Cardiac Imaging Research Group"
      }
    }
    """
    if not callable(query_model):
        raise TypeError("query_model is not a models.Model.objects.get function")

    tree={}
    try:
        for child_id in ids:
            tree[child_id] = {'name': query_model(pk=child_id).name}
            if ids[child_id]:
                tree[child_id]['children'] = get_tree_leaves(ids[child_id], query_model)
    except Exception as e:
        print(e)
    return tree

class Organisation(models.Model):
    name = models.TextField(blank=False)
    description = models.TextField(blank=True, default='')
    site = models.URLField('URL of website', blank=True, default='')
    #~ #Currently is not used, may be used for performance ?
    #~ independent = models.BooleanField(default=False, help_text='If it can exist without other organisations.') #If it is can only be the root tail node in a relationship graph
    abbreviation = models.CharField(max_length=30, blank=True, default='')
    address = models.TextField(blank=True, default='')
    insightly_id = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_child_ids(self):
        """Get ids all child organisations and construct a dictionary in a tree structure"""
        return get_child_ids_of(self.pk)

    def get_parent_ids(self):
        """Get current organisation's top organisation"""
        return get_parent_ids_of(self.pk)

    def get_root_id(self):
        """Get current organisation's top organisation"""
        parents = get_parent_ids_of(self.pk)
        if len(parents):
            return parents[-1]
        else:
            return self.pk

    @property
    def children(self):
        """Get all children of an organisation. Default is only top.
           When flatten=True, get all children no matter which level.
        """
        return self.get_children(flatten=False)

    def get_children(self, flatten=False):
        """Get all children of an organisation. Default is only top.
           When flatten=True, get all children no matter which level.
        """
        if flatten:
            ids = flat_ids(self.get_child_ids(), [])
        else:
            ids = self.get_child_ids()
        return [Organisation.objects.get(pk=org_id) for org_id in ids]

    def has_children(self):
        """Just check if there is any child organisation"""
        from .relationship import Relationship
        return len(Relationship.as_end('Organisation', self)) > 0

    def get_tree(self):
        """Get children Organisations in a tree structure"""
        return get_tree_leaves(self.get_child_ids(), Organisation.objects.get)

    def get_all_services(self):
        """Get all services this Organisation uses"""
        accounts = self.get_all_accounts()
        services = []
        for account in accounts:
            services.extend(account.role.get_all_services())
        return services

    def get_service(self, name=None):
        """Get all instances of a service this Organisation uses"""
        if not name:
            return []

        accounts = self.get_all_accounts()
        services = []
        for account in accounts:
            result = account.role.get_service(name=name)
            if result and len(result):
                services.append(result)
        return services

    def get_all_accounts(self):
        """Get all accounts this Organisation pays"""
        from .person import Account
        return Account.objects.all().filter(billing_org__pk=self.pk)

    def get_extended_accounts(self):
        """Similar to get_all_accounts but for reporting-frontend as a temporary solution"""
        accounts = self.get_all_accounts()
        extended = {}
        for account in accounts:
            extended[account.username] = dict(
               role_id= account.role.id,
               fullname=account.role.person.full_name,
               organisation=account.role.organisation.name,
               email=account.role.email)
        return extended

    def get_all_roles(self):
        """Get all roles under this organisation"""
        roles = list(self.role_set.all())
        ids = flat_ids(self.get_child_ids(), [])
        for child_id in ids:
            roles.extend(Organisation.objects.get(pk=child_id).role_set.all())
        return roles


    @classmethod
    def get_tops(cls, rel_type_name='Organisation'):
        """Get top organisations by querying relationship type

           The default relationtype for this query is 'Organisation'
           which can be replaced if the relationship fixture is not used
        """
        from .relationship import Relationship
        ids = Relationship.tail_only(rel_type_name)
        if len(ids):
            return Organisation.objects.filter(id__in=ids)
        else:
            return [] #this may need some check for consistence

    @classmethod
    def get_billing_organisations(cls):
        """Get unique organisations from Account table

           The default relationtype for this query is 'Organisation'
           which can be replaced if the relationship fixture is not used
        """
        from .person import Account
        biller_ids = [org for org in Account.objects.values_list('billing_org_id', flat=True).distinct()]
        return Organisation.objects.filter(id__in=biller_ids)
