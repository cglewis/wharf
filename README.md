[wharf](http://cglewis.github.io/wharf)
=====

![Wharf L](https://raw.github.com/cglewis/wharf/master/wharf/static/wharf_icon.png "Wharf")

Wharf is an open-source Software-as-a-Service platform built with the power of Docker to enable any Dockerfile and some basic metadata to become an on-demand service in the cloud.

[Demo of Wharf Running](http://dockerwharf.com)

Adding a Service
================

##### Import a Github repository via the clone URL:
```
i.e. https://github.com/cglewis/wharf-services-example.git
```

Option 1
  
```
|─Service1
  |─client
    |─client.txt
    └─test.py (this should be whatever is specified in the client.txt, see below)
  |─docker
    └─Dockerfile
  |─html
    |─about.html
    |─body.html
    └─link.html
  └─description.txt
└─Service2
  |─client
    |─client.txt
    └─test.py (this should be whatever is specified in the client.txt, see below)
  |─docker
    └─Dockerfile
  |─html
    |─about.html
    |─body.html
    └─link.html
  └─description.txt
```

Option 2

```
|─Service1
  └─Dockerfile
└─Service2
  └─Dockerfile
```

Option 3

```
|─Dockerfile
```

##### Upload a zip for tarball:

Create a .zip or .tar.gz of your service.

```
|─Service1
  |─client
    |─client.txt
    └─test.py (this should be whatever is specified in the client.txt, see below)
  |─docker
    └─Dockerfile
  |─html
    |─about.html
    |─body.html
    └─link.html
  └─description.txt
```

##### Import a docker index container via the index.docker.io URL:
```
i.e. https://index.docker.io/u/aespinosa/jenkins/
```


Metadata
========

#### description.txt

Contains a brief description of the service.
```
i.e.
  ElasticSearch, distributed restful search and analytics.
```

#### client/client.txt

The first line is the language of the client, the second line is the file of the example client.  Any other files needed in the client folder can also be included.
```
i.e.
  python
  test.py
  
i.e. test.py
  from pyes import *
  conn = ES('127.0.0.1:49153')
  print "connected successfully"
```

#### docker/Dockerfile

Dockerfile that actually builds the container needed to run the service, this should have an expose port so that the service is accessible remotely.  Any other needed files in the docker folder can also be included.
```
i.e.
  FROM ubuntu
  MAINTAINER Charlie Lewis <charlie.lewis42@gmail.com> 

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
```

#### html/about.html

A brief chunk of prose on what the service is.
```
i.e.
  Elasticsearch uses Lucene under the covers to provide the most powerful full text search capabilities available in any open source product. Search comes with multi-language support, a powerful query language, support for geolocation, context aware did-you-mean suggestions, autocomplete and search snippets.
```

#### html/body.html

A more in depth chunk of prose detailing the service.
```
i.e.
  Elasticsearch uses Lucene under the covers to provide the most powerful full text search capabilities available in any open source product. Search comes with multi-language support, a powerful query language, support for geolocation, context aware did-you-mean suggestions, autocomplete and search snippets.
```

#### html/link.html

A single line that contains a URL for the service and a name for the link.
```
i.e.
  http://www.elasticsearch.org/ ElasticSearch
```

Special thanks to [@kfoss](http://github.com/kfoss) for contributing the artwork for Wharf!

[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/cglewis/wharf/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

