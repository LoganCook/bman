from ..models import Price
from .helpers import convert_qs, convert_list


def list(request):
    """List of all records of Price with their native fields"""
    return convert_qs(Price.objects.all(), Price.get_default_fields())


def list_for_display(request):
    """List of all records of Price with their native fields plus product name"""
    fields = Price.get_default_fields()
    prices = Price.objects.select_related('product').all()
    results = []
    for price in prices:
        result = {}
        for field in fields:
            result[field] = getattr(price, field)
        result['product'] = price.product.name
        result['product_no'] = price.product.no
        results.append(result)
    return convert_list(results)
