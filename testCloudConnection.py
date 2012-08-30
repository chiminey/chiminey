'''
    Created on Jul 6, 2012
    
    @author: iman
    '''


from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

from libcloud.compute.base import NodeImage
from libcloud.compute.deployment import ScriptDeployment
from libcloud.compute.deployment import MultiStepDeployment, ScriptDeployment, SSHKeyDeployment
import os

def printSummary(title, list,printlistsize=0, subtitle=""):    
    listsize = len(list)
    if printlistsize <= 0 or printlistsize > listsize:
        printlistsize = listsize
    
    print (title, listsize)
    if not subtitle == "":
        print(subtitle)
    count=0
    while count < printlistsize:
        print('Instance',count+1,':',list[count])
        count += 1
    print ()


def getIP (name):
    ip = ''
    while name == '' or ip == '':
        nodes = conn.list_nodes()
        for i in nodes:
            if i.name == name and len(i.public_ips) > 0:   
                print ('length ',len(i.public_ips))
                ip = i.public_ips[0]
                break
    
    total_nodes = len(nodes)
    printSummary("Total NeCTAR myInstaces:", nodes)
    
    return ip



EC2_ACCESS_KEY="2cfcd878737d4ba6c71330b84e3018d7"
EC2_SECRET_KEY="2b847b4b-7582-ca45-40eb-e9066ce9f830"
# EC2_URL=http://nova.rc.nectar.org.au:8773/services/Cloud

if __name__ == "__main__":
    OpenstackDriver = get_driver(Provider.EUCALYPTUS)
    print("Connecting...",OpenstackDriver)
    conn = OpenstackDriver(EC2_ACCESS_KEY, secret=EC2_SECRET_KEY,
                           host="nova.rc.nectar.org.au", secure=False, port=8773,
                           path="/services/Cloud")
    print ("Connected")
    
    images = conn.list_images()
    printSummary("Total NeCTAR Images: ", images, printlistsize=0, subtitle="Top Five NeCTAR Images")
    
    
    
    sizes = conn.list_sizes()
    total_sizes = len(sizes)
    printSummary("Total NeCTAR Instaces Types:", sizes)
    
    
    image1 = [i for i in images if i.id == 'ami-0000000d'][0]
    size1 = [i for i in sizes if i.id == 'm1.small'][0]
    
    name = ''
    ip = ''
    import time
    import sys, traceback

    try:
        #ssh_pubkey_location = '/home/iyusuf/.ssh/cloudenable_key.pub'
        #ssh_nectar_key_location = '/home/iyusuf/.ssh/nectar_id'
        #f = open(ssh_pubkey_location, 'r')
        #pubkey = f.readline() # read from file
        #from libcloud.compute.base import NodeAuthSSHKey
        #k = NodeAuthSSHKey(pubkey)
        #print 'Authentication', pubkey
        
        #sd = SSHKeyDeployment(open(os.path.expanduser("~/.ssh/cloudenable_key.pub")).read())
        # a simple script to install puppet post boot, can be much more complicated.
        #script = ScriptDeployment("apt-get -y install puppet")
        # a task that first installs the ssh key, and then runs the script
        #msd = MultiStepDeployment([sd])
        new_instance = conn.create_node(name="New Centos Node",size=size1,image=image1,  ex_keyname='nectar_key', ex_securitygroup='ssh')
            #  while len(new_instance.public_ips) <= 0:
        #time.sleep(2)
        
        #name = new_instance.name

        print ('Name',new_instance.name)
        print ('Waiting for IP')
        
        #ip = getIP(name)
        print ('IP Address', ip)
    except Exception:
        print ('Unable to create environemnt. NeCTAR Quota may be exceeded')
        traceback.print_exc(file=sys.stdout)
    

    
    #for i in nodes:
        #print ('Rebooting ...',i)
        #conn.reboot_node(i)    
        #print ('Rebooted',i)
    
    # provider_locations = conn.list_locations()
    
#i-000020b7
    nodes = conn.list_nodes()
    for i in nodes:
        print "Node",i
        if len(i.public_ip) > 0:
            if i.public_ips[0] != '115.146.94.184':
                print (i, 'to be destroyed')    
                #conn.destroy_node(i)
    
    # counr = 0
    # while count < 2:
    
    #script = ScriptDeployment("pip install paramiko")
    #deploying = conn.deploy_node(name='test', image=image1, size=size1, deploy=script)


