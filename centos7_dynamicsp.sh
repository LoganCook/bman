#!/bin/bash

yum -y install epel-release
yum -y update

yum -y install gcc nginx vim screen
yum -y install python34 python34-devel python-pip
# packages for AAD - the dependency of ersaDynamics
yum -y install openssl-devel libffi-devel

pip install --upgrade virtualenv

# install package
PDIR=/usr/lib/django_dynamicsp
mkdir -p $PDIR/package

cd $PDIR
# install the latest commit
curl -sL https://github.com/eResearchSA/bman/archive/dynamics.tar.gz | tar -xz -C package --strip-components=1

virtualenv -p python3 env
source env/bin/activate
pip install pip --upgrade
pip install https://github.com/eResearchSA/ersaDynamics/archive/master.zip
pip install -r package/requirements_dynamicsp.txt
deactivate

chown -R nginx:nginx $PDIR
PORT=8001

cat > /usr/lib/systemd/system/gunicorn.dynamicsp.service <<EOF
[Unit]
Description=Gunicorn daemon for serving dynamicsp
Requires=gunicorn.dynamicsp.socket
After=network.target

[Service]
Type=simple
User=nginx
Group=nginx
WorkingDirectory=$PDIR/package
Environment=PATH=$PDIR/env/bin
ExecStart=$PDIR/env/bin/gunicorn --error-logfile /var/log/gunicorn/dynamicsp_error.log --log-level info runner.dynamicsp_wsgi
ExecReload=/bin/kill -s HUP \$MAINPID
ExecStop=/bin/kill -s TERM \$MAINPID
RuntimeDirectory=gunicorn
PrivateTmp=true
PIDFile=/run/gunicorn/dynamicsp.pid

[Install]
WantedBy=multi-user.target
EOF

cat > /usr/lib/systemd/system/gunicorn.dynamicsp.socket <<EOF
[Unit]
Description=gunicorn socket to gunicorn.dynamicsp

[Socket]
ListenStream=/run/gunicorn/dynamicsp.socket
ListenStream=0.0.0.0:$PORT

[Install]
WantedBy=sockets.target
EOF

cat > /etc/nginx/conf.d/dynamicsp.conf <<EOF
server {
    listen 80;
    server_name bman.reporting.ersa.edu.au;
    location / {
        proxy_pass http://localhost:$PORT;
        proxy_http_version 1.1;
        proxy_redirect off;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

nginx_location=bman
cat > /etc/nginx/default.d/dynamicsp.conf <<EOF
location /$nginx_location {
    proxy_http_version 1.1;
    proxy_set_header SCRIPT_NAME /$nginx_location;
    proxy_pass http://localhost:$PORT;
}
EOF

mkdir /var/log/gunicorn
chown nginx:nginx /var/log/gunicorn

systemctl enable nginx
systemctl start nginx

systemctl enable gunicorn.dynamicsp.socket
systemctl start gunicorn.dynamicsp.socket

echo "Instance bootstrap completed. Need to update $PDIR/package/runner/dynamicsp.py"
