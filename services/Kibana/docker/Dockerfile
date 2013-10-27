FROM ubuntu
MAINTAINER Charlie Lewis <charliel@lab41.org> 

ENV REFRESHED_AT 2013-10-25
RUN sed 's/main$/main universe/' -i /etc/apt/sources.list
RUN apt-get update
RUN apt-get upgrade -y

# Keep upstart from complaining
RUN dpkg-divert --local --rename --add /sbin/initctl
RUN ln -s /bin/true /sbin/initctl

# python
RUN apt-get install -y python-software-properties
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:fkrull/deadsnakes
RUN apt-get update
RUN apt-get install -y python2.7

# kibana
RUN apt-get install -y wget
RUN apt-get install -y zip 
RUN wget http://download.elasticsearch.org/kibana/kibana/kibana-latest.zip  
RUN unzip kibana-latest.zip
ADD config.js /kibana-latest/

EXPOSE 8000

ENTRYPOINT cd /kibana-latest; python -m SimpleHTTPServer
