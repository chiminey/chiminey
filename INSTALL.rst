virtualenv . -no-site-packages
source bin/activate
python bootstrap.py
bin/buildout
cp bdphpcprovider/settings_changeme.py bdphpcprovider/settings.py # and edit as needed
bin/django syncdb
bin/django migrate
bin/django runserver
