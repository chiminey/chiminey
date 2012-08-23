
Installation:

sudo yum install python-devel
sudo yum install gcc
sudo easy_install virtualenv
virtualenv --no-site-packages .
source bin/activate
pip install -r requirements.txt
python mc.py --help
