# bman
A Django application to collect and provide some information at eRSA.

It contains:

0. [settings example](demo/settings.py.demo)

  This provides a template for an actual setting.py. At least, it needs database settings and SECRET_KEY.
0. [Models](bman/README.md)

It will contain:

0. API for others to call.

##Deployment for testing

It needs to set up web server, wsgi server and database.

###Web server
The package can be served by, for example, __nginx__ (proxy) + __gunicorn__.

If deploy on a CentOS 7 cloud instance, [script](centos7.sh) can be used to set up __nginx__ and __gunicorn__.
_Note_: this script does not do everything to get the application up running as database connection
information is not handled by it. This is better done after boot (manual work).

After creating `demo/setting.py` with the correct information (see below __Prepare database__), assume package has been copied in `/usr/lib/django_bman/pacakge` in
a virtual environment in `/usr/lib/django_bman/env`, then the application can be served by running these commands:

```shell
PDIR=/usr/lib/django_bman
cd $PDIR/package
source env/bin/acative
env/bin/gunicorn demo.wsgi
```

###Prepare database
0. Create user and database:
    ```sql
    --Run from a sql file or in database
    CREATE USER bman WITH ENCRYPTED PASSWORD "SOMEPASSWD";
    CREATE DATABASE bman OWNER bman;
    ```

    ```python
    #Put database information into /usr/lib/django_bman/package/demo/settings.py
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'bman',
            'HOST': '127.0.0.1',
            'USER': 'bman',
            'PASSWORD': 'SOMEPASSWD'
        }
    }
    ```

    ```shell

    sudo su
    cd /usr/lib/django_bman/package
    source ../env/bin/activate
    python manage.py migrate
    python manage.py loaddata --app bman catalog relationshiptype
    # If there is initial data
    python manage.py loadcsv /somepath/init_data.csv
    ```

##Start to listen to the socket
```shell
sudo systemctl start gunicorn.bman.socket
sudo systemctl enable gunicorn.bman.socket
```
