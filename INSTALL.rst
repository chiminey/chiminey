virtualenv . -no-site-packages
source bin/activate
python bootstrap.py
bin/buildout
cp computescheduler/settings_changeme.py computescheduler/settings.py # and edit as needed
bin/django syncdb
bin/django migrate
bin/django runserver
