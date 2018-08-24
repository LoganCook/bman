import jwt
import requests

from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate

from django.conf import settings


def wrap_public_key(public):
    """Format a key string into X509 cert"""
    return "-----BEGIN CERTIFICATE-----\n%s\n-----END CERTIFICATE-----\n" % public


def decode(access_token):
    """Decode an access token

    If access_token has been decoded successfully, returns the token object,
    otherwise, throws jwt.exceptions.
    """
    return jwt.decode(access_token.encode('ascii'), public_key, audience=settings.OIDC_RESOURCE, algorithms=alg)


# General preparation
URLS_FOR_KEYS = settings.OIDC_AUTHORITY_HOST_URL + '/discovery/keys'
keys = requests.get(URLS_FOR_KEYS).json()
# ADFS should have only one key
assert len(keys['keys']) == 1
alg = keys['keys'][0]['alg']
x5c = keys['keys'][0]['x5c'][0]
pub_key = wrap_public_key(x5c)
cert_obj = load_pem_x509_certificate(pub_key.encode('ascii'), backend=default_backend())
public_key = cert_obj.public_key()
