FROM daald/ubuntu32:vivid
# prism requires 32bit java
# based on rastasheep/ubuntu-sshd and mseve/prism

MAINTAINER Ian Thomas <ianedwardthomas@gmail.com>

ARG PASSWORD=root
ENV WORKDIR /home/prism
ENV PRISMVERSION 4.0
ENV PRISM_DOWNLOAD_URL http://www.prismmodelchecker.org/dl/prism-${PRISMVERSION}-linux.tar.gz
#ENV PASSWORD root

# Configure user environment
ENV PATH ${WORKDIR}/prism-${PRISMVERSION}-linux/bin:$PATH

# Install debian packages
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get -y  update && \
    apt-get -y  --no-install-recommends install software-properties-common \
                vim \
                libxi6 \
                libxrender1 \
                libxtst6 \
                curl \
                make \
                sudo \
                gcc \
                g++ \
                openssh-server

# Install Java
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections
RUN add-apt-repository -y ppa:webupd8team/java && \
    apt-get -y  update && \
    apt-get -y  --no-install-recommends install oracle-java8-installer \
    	       	   	   oracle-java8-set-default && \
    apt-get -y  clean

RUN mkdir /var/run/sshd #nocache

RUN echo 'root:$PASSWORD' |chpasswd
#RUN sed -ri 's/^PermitRootLogin\s+.*/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -ri 's/UsePAM yes/#UsePAM yes/g' /etc/ssh/sshd_config

RUN echo "Ciphers aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes128-ctr" >> /etc/ssh/sshd_config

RUN echo "MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,umac-128-etm@openssh.com,hmac-sha2-512,hmac-sha2-256,hmac-ripemd160,hmac-sha1" >> /etc/ssh/sshd_config
RUN echo "KexAlgorithms diffie-hellman-group-exchange-sha256,diffie-hellman-group14-sha1,diffie-hellman-group-exchange-sha1" >> /etc/ssh/sshd_config

# Create prism user
RUN adduser --disabled-password --gecos "" prism
RUN passwd -l prism
ADD prismsudo /etc/sudoers.d/prism
RUN chmod 440 /etc/sudoers.d/prism
RUN chown root:root /etc/sudoers.d/prism
RUN echo "prism:$PASSWORD" | chpasswd prism

# Download and install PRISM
WORKDIR ${WORKDIR}
RUN curl -O ${PRISM_DOWNLOAD_URL}
RUN tar xzvf prism-${PRISMVERSION}-linux.tar.gz
RUN cd prism-${PRISMVERSION}-linux && ./install.sh
ADD profile ${WORKDIR}/.profile
RUN chown -R prism:prism ${WORKDIR}/

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
