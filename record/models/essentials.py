import datetime
import logging

from django.db import models
from django.db.models import F, Prefetch, Sum

logger = logging.getLogger(__name__)


class Account(models.Model):
    """CRM Account entities in maximal of two levels"""
    dynamics_id = models.CharField(max_length=32, null=False, blank=False)
    name = models.CharField(max_length=200, null=False, blank=False)
    parent = models.ForeignKey('self', null=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_tops(cls):
        return cls.objects.filter(parent__isnull=True)

    @classmethod
    def get_children_of(cls, pid):
        return cls.objects.filter(parent_id=pid)

    @classmethod
    def list(cls):
        """Get instances of Account with parent populated"""
        return Account.objects.select_related('parent').all()

    @classmethod
    def get_hierarchy(cls):
        """Get values of Account instance in a hierarchical dict

        { name1: {
                    id: 1234,
                    name: blar,
                    dynamics_id: blar,
                    children: [{
                                 id: 345,
                                 parent_id: 1234,
                                 name: blar,
                                 dynamics_id: blar
                              }]
                 },
          name2: {},
          ...
        }
        """
        id_to_name = {}
        result = {}
        values = Account.objects.all().values()
        for acc in values:
            if acc['parent_id']:
                result[id_to_name[acc['parent_id']]]['children'].append(acc)
            else:
                # Assume names at the top level are unique
                result[acc['name']] = acc
                del result[acc['name']]['parent_id']
                result[acc['name']]['children'] = []
                id_to_name[acc['id']] = acc['name']
        return result

    @classmethod
    def get_by_dynamics_id(cls, did):
        return Account.objects.get(dynamics_id=did)

    @property
    def children(self):
        return Account.objects.filter(parent_id=self.pk).all()

    def assign_manager(self, contact):
        if self.parent:
            raise TypeError('Only top account can have managers: %s is not a top account' % self.name)
        Manager.objects.create(account=self, contact=contact)

    def has_manager(self, contact):
        return Manager.objects.filter(account_id=self.pk, contact_id=contact.pk).exists()

    @property
    def orders(self):
        return Order.objects.filter(biller_id=self.pk).all()


class Contact(models.Model):
    """Contact, a person"""
    dynamics_id = models.CharField(max_length=32, null=False, blank=False)
    account = models.ForeignKey(Account)
    name = models.CharField('full name', max_length=100, null=False, blank=False)
    email = models.EmailField('email address', null=False, blank=False)

    def __str__(self):
        return '%s (%s)' % (self.name, self.email)

    @staticmethod
    def is_ersa_email(email):
        return email.endswith('ersa.edu.au')

    @classmethod
    def get_by_email(cls, email):
        # shortcut
        if cls.is_ersa_email(email):
            return Contact(name='Admin', email=email)
        return cls.objects.get(email=email)

    @property
    def is_admin(self):
        return self.is_ersa_email(self.email)

    def get_managed_account_id(self):
        """Get id of an Account current Contact managing"""
        try:
            return Manager.objects.get(contact__email=self.email).account_id
        except Manager.DoesNotExist:
            return None


class Manager(models.Model):
    """Contact works as a top Account manager"""
    account = models.ForeignKey(Account)
    contact = models.ForeignKey(Contact)

    @classmethod
    def get_managed_account_id(cls, email):
        try:
            return cls.objects.get(contact__email=email).account_id
        except cls.DoesNotExist:
            return None


class Product(models.Model):
    """Simple or composed product

    no: product number, user defined, unique
    parent: used in either pseudo or super product
    type: used in deciding how calculation is done
    """
    dynamics_id = models.CharField(max_length=32, null=False, blank=False)
    name = models.CharField(max_length=200, null=False, blank=False)
    no = models.CharField(max_length=200, null=True)
    # type - Miscellaneous Charges:pseudo product
    # type - Serveice: cost is calculated by usage and time
    # type - Flat Fees: cost is calculated by time only, not usage
    # type - Sales Inventory: same as Service
    type = models.CharField(max_length=25)
    # structure: Product, Bundle or Family, not very useful
    structure = models.CharField(max_length=10)
    parent = models.ForeignKey('self', null=True)

    class Meta:
        indexes = [models.Index(fields=['no'])]

    def __str__(self):
        composed = ', composed part' if self.parent else ''
        return ('%s, type=%s, (%s)%s' % (self.name, self.type, self.no, composed)).rstrip()

    @property
    def is_composed(self):
        return Product.objects.filter(parent_id=self.pk).exists()

    @classmethod
    def get_by_no(cls, product_no):
        return Product.objects.get(no=product_no)

    def get_composition(self):
        return Product.objects.filter(parent_id=self.pk).all()

    def get_price(self, list_name):
        """Get the latest price"""
        return Price.objects.filter(product_id=self.pk, list_name=list_name).first().amount

    def get_prices(self):
        return Price.objects.filter(product_id=self.pk).all()

    def get_historical_prices(self, start, end):
        # both start and end are timestamp
        return Price.objects.filter(product_id=self.pk, date__gt=start, date__lte=end).all()

    def get_price_finder(self):
        return PriceFinder(list(self.get_prices()))


class PriceFinder(object):
    def __init__(self, price_objs):
        self.prices = {}
        for price in price_objs:
            if price.list_name not in self.prices:
                self.prices[price.list_name] = []
            self.prices[price.list_name].append({"date": price.date, "amount": price.amount})

    def get_latest_price(self, list_name):
        return self.prices[list_name][0]['amount']

    def get_price(self, list_name, start, end):
        """Pop price one by one from latest to oldest until find a price fits in the range"""
        for date_amount in self.prices[list_name]:
            if start >= date_amount['date']:
                return date_amount['amount']
            elif start < date_amount['date'] and end >= date_amount['date']:
                return date_amount['amount']
        raise ValueError('Cannot find a price for %s between %d - %d' % (list_name, start, end))


class Order(models.Model):
    """Summary of purchases"""
    dynamics_id = models.CharField(max_length=32, null=False)
    name = models.CharField(max_length=200)
    no = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    biller = models.ForeignKey(Account)
    manager = models.ForeignKey(Contact)
    price_list = models.CharField(max_length=100)
    record_date = models.IntegerField(null=True, default=int(datetime.datetime.now().timestamp()))  # timestamp, not sure if this is needed for what

    def __str__(self):
        return '%s %s %s %s %s %s %s' % (self.dynamics_id, self.name, self.no, self.description, self.biller.name, self.manager.name, self.price_list)

    @property
    def orderlines(self):
        return Orderline.objects.filter(order_id=self.pk).all()

    def get_orderlines_by_product(self, product):
        return Orderline.objects.filter(order_id=self.pk, product_id=product.pk).all()


class Orderline(models.Model):
    """Detail of a purchase

    identifier: a token links this purchase record to usage data and for
                further grouping
    """
    order = models.ForeignKey(Order)
    product = models.ForeignKey(Product)
    quantity = models.IntegerField()
    # Even Order and Orderline once created do not change, price can change.
    # So, price here is the original price when ingested, only acts as place
    # holder, actual price for calculating fee is from table Price.
    price = models.FloatField()
    # In CRM contract, there is only one identifer field. But usage data
    # sometimes need to be further grouped, therefore this identifier can
    # be composed from the identifer of contract in CRM and extra usage
    # identifiers. So when ingesting, when usage-identifiers exists, both
    # contract in CRM and usage have to on hand at the same time
    identifier = models.CharField(max_length=512, null=False, blank=False)

    class Meta:
        unique_together = ("order", "product", "identifier")

    def __str__(self):
        return '%s %s %s %d %.2f' % (self.order.name, self.product.name, self.identifier, self.quantity, self.price)

    @classmethod
    def get_by_product_no(cls, product_no):
        return cls.objects.filter(product__no=product_no).select_related('order').all()

    @classmethod
    def get_by_identifier(cls, identifier, product_no):
        # make use of select_related otherwise we can use get
        return cls.objects.filter(identifier=identifier, product__no=product_no).select_related('order')[0]


class Price(models.Model):
    """Price of product and the history of prices collected from CRM productpricelevel entity

    Same product can appear on different price lists
    date: when a price amount has changed
    """
    # productpricelevelid
    dynamics_id = models.CharField(max_length=32, null=False)
    list_name = models.CharField(max_length=100)
    product = models.ForeignKey(Product)
    unit = models.CharField(max_length=20)
    amount = models.FloatField()
    date = models.IntegerField(default=int(datetime.datetime.now().timestamp()))

    class Meta:
        unique_together = ("list_name", "product", "date")
        ordering = ['list_name', 'product_id', '-date']

    @classmethod
    def get_default_fields(cls):
        return ('id', 'dynamics_id', 'list_name', 'product_id', 'unit', 'amount', 'date')


class Usage(models.Model):
    """Raw usage data of each product in period"""
    start = models.IntegerField()
    end = models.IntegerField()
    orderline = models.ForeignKey(Orderline)

    class Meta:
        abstract = True

    @classmethod
    def get(cls, start, end):
        return cls.objects.filter(start__gte=start, end__lte=end).select_related('orderline').all()

    @classmethod
    def get_default_fields(cls):
        return ('id', 'start', 'end')

    @classmethod
    def get_usage_set(cls):
        """Get a name string of usage class for orderline"""
        return cls.__name__.lower() + '_set'

    @classmethod
    def create_base_qs(cls, start, end):
        """Create a base query to include fee and usage"""
        # It needs fee and usage order
        # derived class can add more prefetch_related if needed

        usage_qs = cls.objects.filter(start__gte=start, end__lte=end)
        orderline_id_qs = usage_qs.distinct().values_list('orderline_id', flat=True)
        fee_qs = Fee.objects.filter(start__gte=start, end__lte=end, orderline_id__in=orderline_id_qs)

        prefetch_fee = Prefetch('fee_set', queryset=fee_qs)
        prefetch_usage = Prefetch(cls.get_usage_set(), queryset=usage_qs)

        return Orderline.objects.filter(pk__in=orderline_id_qs).select_related('order__biller', 'order__manager__account').prefetch_related(prefetch_usage, prefetch_fee) \
            .annotate(name=F('order__name'), account=F('order__biller__name'), unit=F('order__manager__account__name'), managerName=F('order__manager__name'), managerEmail=F('order__manager__email'))

    @classmethod
    def get_extract_config_method(cls):
        # derived classes should return a function takes only one positional argument orderline
        # extract_config(orderline)
        return None

    @classmethod
    def get_sum_usage_method(cls):
        # derived classes should return a function takes only one positional argument orderline
        # sum_usage(orderline)
        raise NotImplementedError

    @classmethod
    def fetch_related(cls, orderline_qs):
        """Merge orderline, usage and extra information of orderline if it has"""
        # Derived usage class has to provide sum_usage
        def sum_fee(qs):
            try:
                return qs.values('orderline_id').annotate(totalFee=Sum('amount'))[0]
            except IndexError:
                return {}

        def extract_value(instance, values):
            result = {}
            for value in values:
                result[value] = getattr(instance, value)
            return result

        main_fields = 'name', 'account', 'unit', 'managerName', 'managerEmail', 'price', 'identifier'
        extract_config = cls.get_extract_config_method()
        sum_usage = cls.get_sum_usage_method()
        results = []
        for ol in orderline_qs:
            result = extract_value(ol, main_fields)
            result.update(sum_fee(ol.fee_set))
            result.update(sum_usage(ol))
            if callable(extract_config):
                result.update(extract_config(ol))
            results.append(result)
        return results

    @classmethod
    def create_fee_base_qs(cls, start, end):
        return Fee.objects.filter(orderline_id__in=cls.objects.filter(
            start__gte=start, end__lte=end).values('orderline_id'))


class Fee(models.Model):
    # bill can have different periods than usage data
    orderline = models.ForeignKey(Orderline)
    start = models.IntegerField()
    end = models.IntegerField()
    amount = models.FloatField()

    class Meta:
        unique_together = ("orderline", "start", "end")

    @classmethod
    def of_product(cls, product, start=None, end=None):
        return cls.of_product_by_no(product.no, start, end)

    @classmethod
    def of_product_by_no(cls, product_no, start=None, end=None):
        qs = cls.objects.filter(orderline__product__no=product_no).order_by('start')
        if start:
            qs = qs.filter(start__gte=start)
        if end:
            qs = qs.filter(end__lte=end)
        return qs

    @classmethod
    def get_default_fields(cls):
        return ('id', 'start', 'end', 'amount')
