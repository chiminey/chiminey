#!/bin/sh
# version 2.0


WORK_DIR=`pwd`
cd /opt

# Install Java
jdk_version=${1:-8}
ext=tar.gz

readonly url="https://www.oracle.com"
readonly jdk_download_url1="$url/technetwork/java/javase/downloads/index.html"
readonly jdk_download_url2=$(
    curl -s $jdk_download_url1 | \
    egrep -o "\/technetwork\/java/\javase\/downloads\/jdk${jdk_version}-downloads-.+?\.html" | \
    head -1 | \
    cut -d '"' -f 1
)
[[ -z "$jdk_download_url2" ]] && echo "Could not get jdk download url - $jdk_download_url1" >> /dev/stderr

readonly jdk_download_url3="${url}${jdk_download_url2}"
readonly jdk_download_url4=$(
    curl -s $jdk_download_url3 | \
    egrep -o "http\:\/\/download.oracle\.com\/otn-pub\/java\/jdk\/[8-9](u[0-9]+|\+).*\/jdk-${jdk_version}.*(-|_)linux-(x64|x64_bin).$ext"
)

for dl_url in ${jdk_download_url4[@]}; do
    wget --no-cookies \
         --no-check-certificate \
         --header "Cookie: oraclelicense=accept-securebackup-cookie" \
         -N $dl_url
done
JAVA_TARBALL=$(basename $dl_url)
tar xzfv $JAVA_TARBALL

# Install PRISM
PRISM_VERSION=4.3.1
PRISM_DOWNLOAD_URL=http://www.prismmodelchecker.org/dl/prism-${PRISM_VERSION}-linux64.tar.gz

yum -y update
yum -y install glibc.i686 libstdc++.so.6 gcc make

curl -O ${PRISM_DOWNLOAD_URL}
tar xzvf prism-${PRISM_VERSION}-linux64.tar.gz
cd prism-${PRISM_VERSION}-linux64 && ./install.sh
chown -R root:root /opt/prism-${PRISM_VERSION}-linux64
chmod -R 755 /opt/prism-${PRISM_VERSION}-linux64

export PATH=/opt/prism-${PRISM_VERSION}-linux64/bin:$PATH

cd $WORK_DIR
