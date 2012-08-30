USER_NAME = "username" #account name of instance 
PASSWORD = "password"  #account password of instance
PRIVATE_KEY = './myprivatekey.pem'  # The nectar private key
PRIVATE_KEY_NAME = 'nectar_key'
SECURITY_GROUP = ['ssh']
PAYLOAD = "aeao_v1_1_package.tar.gz" # the filename of the package
DEST_PATH_PREFIX="package" # The destination directory for the software to run 
DEPENDS = ['dos2unix','gcc-gfortran','compat-gcc-34-g77.x86_64'] # yum install requirements
COMPILER="g77" # The compiler command
COMPILE_FILE="HRMC" # The file to be compiled (no extension)
PAYLOAD_DIRNAME="AEAO_v1_1" #The directory of the unpackaed payload

SLEEP_TIME = 10 # time to wait before polling finished job in seconds
RETRY_ATTEMPTS = 10 # number of times to try accessing package PID

OUTPUT_FILES = ['output','energy01.dat', \
	'engchn01.dat',\
	'engerr01.dat',\
	'error01.dat',\
	'frnmc01.dat',\
	'frsp301.dat',\
	'grchn01.dat',\
	'grerr01.dat',\
	'spchn01.dat',\
	'sperr01.dat',\
	'sqchn01.dat',\
	'sqerr01.dat',\
	'hrmc01.xyz',\
	'hrmcpr01.xyz',\
	'start01.xyz',\
	'abc',\
	'sqinput.dat']

TEST_VM_IP = '115.146.94.152'
EC2_ACCESS_KEY=""
EC2_SECRET_KEY=""
CLOUD_SLEEP_INTERVAL=5