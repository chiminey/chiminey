USER_NAME = "username" #account name of instance 
PASSWORD = "password"  #account password of instance
PRIVATE_KEY = './myprivatekey.pem'  # The nectar private key
PAYLOAD = "aeao_v1_1_package.tar.gz" # the filename of the package
DEST_PATH_PREFIX="package" # The destination directory for the software to run 
DEPENDS = ['dos2unix','gcc-gfortran','compat-gcc-34-g77.x86_64'] # yum install requirements
COMPILER="g77" # The compiler command
COMPILE_FILE="HRMC" # The file to be compiled (no extension)
PAYLOAD_DIRNAME="AEAO_v1_1" #The directory of the unpackaed payload

SLEEP_TIME = 10 # time to wait before polling finished job in seconds
RETRY_ATTEMPTS = 10 # number of times to try accessing package PID

OUTPUT_FILES = ['output','energy01.dat','spchn01.dat']
TEST_VM_IP = '115.146.94.152'