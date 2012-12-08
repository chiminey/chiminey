yum install python-setuptools
yum install gcc
yum install python-devel
yum install nginx

easy_install virtualenv

virtualenv . -no-site-packages

source bin/activate

python bootstrap.py

bin/buildout

bin/django syncdb

bin/django migrate

_Copy uwsgi.conf from conf/ to /etc/init/uwsgi.conf (CentOS 6) and fix paths_

start uwsgi

_Copy cloudenabling.conf from conf/ to /etc/nginx/conf.d/cloudenabling.conf and fix paths_

_Rename /etc/nginx/conf.d/default.conf to default.conf.bak_

service nginx start

_Ensure firewall service (iptables) is correct to access port 80_
