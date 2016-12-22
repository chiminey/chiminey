#!/bin/sh
# version 2.0


WORK_DIR=`pwd`

JAVA_UPDATE=8u101
JAVA_BUILD=b13
JAVA_VERSION=jdk1.8.0_101
JAVA_COOKIE="Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie"
JAVA_DOWNLOAD_URL="http://download.oracle.com/otn-pub/java/jdk/${JAVA_UPDATE}-${JAVA_BUILD}/jdk-${JAVA_UPDATE}-linux-x64.tar.gz"

yum -y update
yum -y install glibc.i686 libstdc++.so.6 gcc make

# Install Java
cd /opt/
wget --no-cookies --no-check-certificate --header "${JAVA_COOKIE}" "${JAVA_DOWNLOAD_URL}"
tar xzfv jdk-${JAVA_UPDATE}-linux-x64.tar.gz

export PATH=/opt/${JAVA_VERSION}/bin:$PATH 

cd $WORK_DIR
