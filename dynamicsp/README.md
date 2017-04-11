# dynamicsp
A Django application to create APIs for querying MS Dynamics of eRSA. It needs an Azure account for accessing
the instance and manually prepared valid refresh and access tokens.

The [settings file](runner/dynamicsp.py) is a template for creating actual setting files.
When deploy, you at least need to:

1. Update `ALLOWED_HOSTS` if access url is other than localhost. With production deployment, which uses `nginx` as proxy,
   this is not needed.
1. Create a JSON file which contains arguments for connecting an Azure Active Directory Web app / API
   listed below and update `DYNAMICS_CONF` with its path

   ```JSON
   {
        "authorityHostUrl": "https://login.microsoftonline.com",
        "resource": "https://instance.crm6.dynamics.com",
        "tenant": "aad_tenant_id",
        "clientId": "aad_application_client_id",
        "clientSecret": "high_secret"
    }
   ```
1. Update `TOKENS_JSON` with the path of an existing file which has saved refresh and access tokens
   or a newly created one using `ersaDynamics` (see its document - _to be created_). Make sure it is
   web server writable. In production, `nginx` should have write permission.

## Deployment for testing

Either `python manager.py` or `gunicorn`  with `--settings runner.dynamicsp` from project path is OK.

For using __nginx__ (proxy) + __gunicorn__ and on a CentOS 7 cloud instance, [script](centos7_dynamicsp.sh)
can be used to set up __nginx__ and __gunicorn__.
_Note_: this script does not do everything to get the application up running as configuration files are not handled by it.
This is better done after boot (manual work).

Assume package has been copied into `/usr/lib/django_dynamicsp/pacakge` and `runner/dynamicsp.py` has been update with
correct information and a virtual environment has been created in `/usr/lib/django_dynamicsp/env`, then the application
can be served by running these commands:

```shell
PDIR=/usr/lib/django_dynamicsp
cd $PDIR/package
source env/bin/acative
gunicorn runner.dynamicsp_wsgi
```

## Note

Given the ConnectionRoles used to describe relationships between Contacts and Orders will not change once
have been created, for performance reason, instead of collecting them at run time, their Dynamics Ids are
set in settings. You of course can get these values by calling `views.get_order_roleid` with names. The
roles and their Dynamics Ids are set in settings are: `PROJECT_ADMIN_ROLE`, `PROJECT_LEADER_ROLE` and
`PROJECT_MEMBER_ROLE`.
