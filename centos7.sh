#!/bin/bash

yum -y install epel-release
yum -y update
yum -y install python-pip gcc nginx vim screen
# run database on the same server, the version is from yum: 9.2
yum -y install python34 python34-devel postgresql-devel postgresql-server postgresql postgresql-libs

postgresql-setup initdb

cat > /var/lib/pgsql/data/pg_hba.conf << EOF
local all all peer
host all all 127.0.0.1/32 md5
EOF

systemctl start postgresql
systemctl enable postgresql

su -l postgres -c "createuser --superuser ec2-user"

pip install pip --upgrade
pip install --upgrade virtualenv

# install package
PDIR=/usr/lib/django_bman
mkdir -p $PDIR/package

cd $PDIR
# install the latest commit
wget -qO - https://github.com/eResearchSA/bman/archive/master.tar.gz | tar -xz -C package --strip-components=1

virtualenv -p python3 env
source env/bin/activate
pip install -r package/requirements.txt
deactivate

chown -R nginx:nginx $PDIR

cat > /usr/lib/systemd/system/gunicorn.bman.service <<EOF
[Unit]
Description=Gunicorn daemon for serving bman
Requires=gunicorn.bman.socket
After=network.target

[Service]
Type=simple
User=nginx
Group=nginx
WorkingDirectory=$PDIR/package
Environment=PATH=$PDIR/env/bin
ExecStart=$PDIR/env/bin/gunicorn --error-logfile /var/log/gunicorn/error.log --log-level info demo.wsgi
ExecReload=/bin/kill -s HUP \$MAINPID
ExecStop=/bin/kill -s TERM \$MAINPID
RuntimeDirectory=gunicorn
PrivateTmp=true
PIDFile=/run/gunicorn/bman.pid

[Install]
WantedBy=multi-user.target
EOF

cat > /usr/lib/systemd/system/gunicorn.bman.socket <<EOF
[Unit]
Description=gunicorn socket to gunicorn.bman

[Socket]
ListenStream=/run/gunicorn/bman.socket
ListenStream=0.0.0.0:8000

[Install]
WantedBy=sockets.target
EOF

cat > /etc/nginx/conf.d/bman.conf <<EOF
server {
    listen 80;
    server_name bman.reporting.ersa.edu.au;
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_redirect off;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

nginx_location=bman
cat > /etc/nginx/default.d/bman.conf <<EOF
location /$nginx_location {
    proxy_http_version 1.1;
    proxy_redirect off;
    proxy_set_header SCRIPT_NAME /$nginx_location;
    proxy_pass http://localhost:8000;
}
EOF

mkdir /var/log/gunicorn
chown nginx:nginx /var/log/gunicorn

systemctl enable nginx
systemctl start nginx

echo "Instance bootstrap completed. Need to create database and user for django app"
