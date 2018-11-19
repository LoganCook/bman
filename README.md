# bman
A set of Django applications to collect and provide service information at eRSA.

It contains two user - service information management applications: [standalone](bman)
and [a proxy](dynamicsp). It also contains an Django command line application to
calculate [usage](usage) of a service. The usage application is mainly for demonstration.

## Serve by a Web server
The package can be served by, for example, __nginx__ (proxy) + __gunicorn__.

If it is deployed on a CentOS 7 cloud instance, [script](centos7.sh) can be used as a starting point
to set up __nginx__ and __gunicorn__ for an application. Basically, it creates a service using __gunicorn__
to run the application and map this service to a URL served by __nginx__.

_Note_: this script does not do everything to get the application up running as database connection
information is not handled by it. This is better done after boot (manual work). The `SECRET_KEY` can be generated using `django.core.management.utils.get_random_secret_key()`.

All the configuration files are assumed coming from `runner` directory. After creating
`runner/bman.py` with the correct information, for a package that has been copied in
`/usr/lib/django_bman/pacakge` and a virtual environment created in
`/usr/lib/django_bman/env`, then the application can be served by
running these commands:

```shell
PDIR=/usr/lib/django_bman
cd $PDIR/package
source env/bin/acative
env/bin/gunicorn runner.usage_wsgi
```

### Start to listen to the socket
```shell
sudo systemctl start gunicorn.bman.socket
sudo systemctl enable gunicorn.bman.socket
```
