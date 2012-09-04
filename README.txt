
Installation:

sudo yum install git
sudo yum install python-devel python-setuptools
sudo yum install gcc
sudo easy_install virtualenv
virtualenv --no-site-packages .
source bin/activate
pip install -r requirements.txt
python mc.py --help

Example
python mc.py create
python mc.py setup --nodeid=42
python mc.py --nodeid=42 --inputdir=input/ --outputdir=output run
python mc.py --nodeid=42 check --outputdir=output
