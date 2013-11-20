FROM ubuntu
MAINTAINER Charlie Lewis <charlie.lewis42@gmail.com>

ENV REFRESHED_AT 2013-10-22
RUN sed 's/main$/main universe/' -i /etc/apt/sources.list
RUN apt-get update
RUN apt-get upgrade -y

# Keep upstart from complaining
RUN dpkg-divert --local --rename --add /sbin/initctl
RUN ln -s /bin/true /sbin/initctl

# sets root password to root, but isn't accessible from the outside
RUN echo 'mysql-server-5.5 mysql-server/root_password password password' | debconf-set-selections
RUN echo 'mysql-server-5.5 mysql-server/root_password_again password password' | debconf-set-selections

RUN apt-get update && apt-get install -y mysql-server && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN sed -i -e"s/^bind-address\s*=\s*127.0.0.1/bind-address = 0.0.0.0/" /etc/mysql/my.cnf

ADD mysql-setup.sh /tmp/mysql-setup.sh
RUN /bin/sh /tmp/mysql-setup.sh

EXPOSE 3306

ENTRYPOINT ["/usr/sbin/mysqld"]
