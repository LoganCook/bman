# bman application
A Django application to collect and provide service information at eRSA.

## Deployment for testing

It needs to set up a web server, a wsgi server and a database.

### Web server
The package can be served by, for example, __nginx__ (proxy) + __gunicorn__.

If deploy on a CentOS 7 cloud instance, [script](centos7.sh) can be used to set up __nginx__ and __gunicorn__.
_Note_: this script does not do everything to get the application up running as database connection
information is not handled by it. This is better done after boot (manual work).

Assuming configuration files are in `runner` directory. After creating
`runner/bman.py` with the correct information (see below __Prepare
database__), assume package has been copied in
`/usr/lib/django_bman/pacakge` in a virtual environment in
`/usr/lib/django_bman/env`, then the application can be served by
running these commands:

```shell
PDIR=/usr/lib/django_bman
cd $PDIR/package
source env/bin/acative
env/bin/gunicorn runner.usage_wsgi
```

### Prepare database
1. Create user and database if use databases other than sqlite:
    ```sql
    --Run from a sql file or in database
    CREATE USER bman WITH ENCRYPTED PASSWORD "SOMEPASSWD";
    CREATE DATABASE bman OWNER bman;
    ```

    ```python
    # Put database information into /usr/lib/django_bman/package/runner/bman.py
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

1. Create tables and load data:
    ```shell

    sudo su
    cd /usr/lib/django_bman/package
    source ../env/bin/activate
    python manage.py migrate
    python manage.py loaddata --app bman catalog relationshiptype
    # If there is initial data
    python manage.py loadcsv /somepath/init_data.csv
    python manage.py ingest /somepath/some_ingestable_data.csv
    ```
   When multiple settings exist in `runner` pacakge, run commands with `--settings`:

   `python manage.py command --settings=runner.bman`

   `settings` should be one of none-wsgi py file.

## Start to listen to the socket
```shell
sudo systemctl start gunicorn.bman.socket
sudo systemctl enable gunicorn.bman.socket
```
