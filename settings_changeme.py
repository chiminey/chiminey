USER_NAME = "username" #account name of instance 
PASSWORD = "password"  #account password of instance
PAYLOAD = "aeao_v1_1_package.tar.gz" # the filename of the package
DEST_PATH_PREFIX="package" # The destination directory for the software to run 
DEPENDS = ['dos2unix','gcc-gfortran','compat-gcc-34-g77.x86_64'] # yum install requirements
COMPILER="g77" # The compiler command
COMPILE_FILE="HRMC.f" # The file to be compiled
PAYLOAD_DIRNAME="AEAO_v1_1" #The directory of the unpackaed payload