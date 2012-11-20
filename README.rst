virtualenv . -no-site-packages
source bin/activate
python bootstrap.py
bin/buildout
bin/django syncdb
bin/django runserver
