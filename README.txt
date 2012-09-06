
Installation:

sudo yum install git
sudo yum install python-devel python-setuptools
sudo yum install gcc
sudo easy_install virtualenv
virtualenv --no-site-packages .
source bin/activate
pip install -r requirements.txt
mkdir ~/.cloudenabling
cp cloudenable/config.sys ~/.cloudenabling/config
# add EC2_ACCESS_KEY and EC2_SECRET_KEY and location and name of private key

Example
cd cloudenable
python mc.py create
python mc.py setup --nodeid=42
python mc.py --nodeid=42 --inputdir=../input/ --outputdir=output run
python mc.py --nodeid=42 check --outputdir=output
python mc.py --nodeid=42 teardown


Notes
- We support python 2.6
- Check with Daniel the version of python that is being used in Physics department
