FROM ubuntu
MAINTAINER Charlie Lewis <charliel@lab41.org> 

ENV REFRESHED_AT 2013-10-25
RUN sed 's/main$/main universe/' -i /etc/apt/sources.list
RUN apt-get update
RUN apt-get upgrade -y

# Keep upstart from complaining
RUN dpkg-divert --local --rename --add /sbin/initctl
RUN ln -s /bin/true /sbin/initctl

RUN apt-get install -y openjdk-6-jdk
RUN apt-get install -y wget
RUN apt-get install -y dpkg
RUN wget --no-check-certificate https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-0.90.2.deb
RUN dpkg -i elasticsearch-0.90.2.deb
RUN /usr/share/elasticsearch/bin/plugin -install mobz/elasticsearch-head
RUN service elasticsearch stop

EXPOSE 9200

ENTRYPOINT ["/usr/share/elasticsearch/bin/elasticsearch", "-f"]
