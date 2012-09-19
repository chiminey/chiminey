
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
python mc.py info
python mc.py create -v 1
python mc.py setup --group=76de47e2573676b113b4338f1012c2742
python mc.py run --group=76de47e2573676b113b4338f1012c2742 --inputdir=../input/ --outputdir=output -seed=42
python mc.py check --group=76de47e2573676b113b4338f1012c2742 --outputdir=output
python mc.py teardown --nodeid=42 
python mc.py teardown -g 76de47e2573676b113b4338f1012c2742
python mc.py teardown_all


Notes
- We support python 2.6
- Check with Daniel the version of python that is being used in Physics department
- PyFilesystem requires at least Python 2.5
