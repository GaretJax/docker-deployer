# Metadata
FROM ubuntu:quantal
MAINTAINER Jonathan Stoppani "jonathan.stoppani@wsfcomp.com"

# Setup environment
ENV DEBIAN_FRONTEND noninteractive
RUN /usr/sbin/locale-gen en_US.UTF-8 && \
	/usr/sbin/update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV DJANGO_SETTINGS_MODULE padi.settings

# Update the system and add additional sources
RUN /usr/bin/apt-get update && \
	/usr/bin/apt-get install -y software-properties-common python-software-properties wget && \
	/usr/bin/add-apt-repository "deb http://archive.ubuntu.com/ubuntu quantal universe" && \
	/usr/bin/apt-get update && \
	/usr/bin/apt-get -y upgrade

# Install required dependencies
RUN /usr/bin/apt-get install -y \
		python-pip \
		libpcre3 libjson0 \
		git-core mercurial \
		libxml2 libxslt1.1 \
		libpython2.7 && \
	/usr/bin/pip install --upgrade pip && \
	/usr/local/bin/pip install --upgrade setuptools wheel

# Add files
ADD https://buildbot.apps.wsf/artifacts/wsfcomp-root-ca.pem /usr/share/ca-certificates/wsfcomp-root-ca.pem

# uWSGI specific user
# Create directories
# Install GeoIP
# Install wsfcomp CA certificate
# Install server script
RUN useradd uwsgi && \
	mkdir -p /srv/deployer && \
	chown uwsgi:uwsgi /srv/deployer && \
	echo wsfcomp-root-ca.pem >> /etc/ca-certificates.conf && \
	update-ca-certificates && \
	cat /usr/share/ca-certificates/wsfcomp-root-ca.pem >> /usr/local/lib/python2.7/dist-packages/pip/cacert.pem
