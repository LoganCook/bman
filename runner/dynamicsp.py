"""
Django settings for dynamicsp project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '19^qvdp3n9y@#g+1-iw&as7!*8kco*qfu$b%(q*9eywuzq1)wb'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'dynamicsp',
)

#For start up, disable all middlewares
MIDDLEWARE_CLASSES = (
#    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
#    'django.contrib.messages.middleware.MessageMiddleware',
#    'django.middleware.clickjacking.XFrameOptionsMiddleware',
#    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'dynamicsp.urls'

WSGI_APPLICATION = 'runner.dynamicsp_wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Australia/Adelaide'

USE_I18N = True

USE_L10N = True

USE_TZ = True

DYNAMICS_CONF = BASE_DIR + '/dyncon.json'
TOKENS_JSON = BASE_DIR + '/saved_tokens.json'

# Hard coded Contact person of an Order's ConnectionRole ids for performance
# views.get_order_roleid is the code to get id
PROJECT_ADMIN_ROLE = '8355863e-85fc-e611-810b-e0071b6685b1'
PROJECT_LEADER_ROLE = '99acba33-f3f7-e611-8112-70106fa3d971'
PROJECT_MEMBER_ROLE = '783fd375-f3f7-e611-8112-70106fa3d971'