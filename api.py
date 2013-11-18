from flask import Flask
from flask import Markup
from flask import render_template
from flask import request
from flask import jsonify

#from docker import client

from os import environ
from os import listdir
from os import path

#import redis
import time

app = Flask(__name__)
app.debug = True

#set defaults

#IMAGE_NAME = "damien/mongodb"
#COMMAND = ["/usr/bin/mongod", "--config", "/etc/mongodb.conf"]
#DOMAIN = "domain"
#HIPACHE_PORT="80"
#EXPOSED_PORT="27017"

#environment variables, must be set in order for application to function
#try:
#    REDIS_PORT=environ["REDIS_PORT"]
#    REDIS_HOST=environ["REDIS_HOST"]
#    HIPACHE_PORT=environ["HIPACHE_PORT"]
#    DOCKER_HOST=environ["DOCKER_HOST"]
#except Exception, e:
#    print e
#    print "environment not properly configured"
#    print environ
#    import sys; sys.exit(1)

#r = redis.StrictRedis(host=REDIS_HOST, port=int(REDIS_PORT))
#c = client.Client(base_url='http://%s:4243' % DOCKER_HOST)

@app.route('/')
def index():
    row = ""
    services = listdir("services")
    for service in services:
        last_modified = ""
        last_modified = time.ctime(path.getmtime("services/"+service))
        description = ""
        # !! TODO try/except
        description_path = "services/"+service+"/description.txt"
        with open(description_path, 'r') as content_file:
            description = content_file.read()
        row += '<tr><td class="rowlink-skip"><a href="saas/'+service+'">'+service+'</a></td><td>'+description+'</td><td><a href="saas/'+service+'">'+last_modified+'</a></td></tr>'
    row = Markup(row)
    return render_template("index.html",row=row)

@app.route('/saas/<service>')
def saas(service):
    about = ""
    body = ""
    link = ""
    link_name = ""
    # !! TODO try/except
    about_path = "services/"+service+"/html/about.html"
    with open(about_path, 'r') as content_file:
        about = content_file.read()
    body_path = "services/"+service+"/html/body.html"
    with open(body_path, 'r') as content_file:
        body = content_file.read()
    link_path = "services/"+service+"/html/link.html"
    with open(link_path, 'r') as content_file:
        link = content_file.read()
    link_a = link.split(" ", 1)
    link = link_a[0]
    link_name = link_a[1]
    return render_template("saas.html",service=service,about=about,body=body,link=link,link_name=link_name)

@app.route('/new', methods=["POST"])
def new():
    container = c.create_container(IMAGE_NAME, COMMAND, ports=[EXPOSED_PORT])
    container_id = container["Id"]
    c.start(container_id)
    container_port = c.port(container_id, EXPOSED_PORT)
    r.rpush("frontend:%s.%s" % (container_id, DOMAIN), container_id)
    r.rpush("frontend:%s.%s" % (container_id, DOMAIN), "http://%s:%s" %(DOMAIN, container_port))
    if HIPACHE_PORT == "80":
        url = "%s:%s" % (DOMAIN, container_port)
    else:
        url="%s:%s" % (DOMAIN, container_port)

    return jsonify(
            url=url,
            port=container_port,
            hipache_port=HIPACHE_PORT,
            id=container_id)

@app.route('/details/<service>/<url>')
def details(url, service):
    client = ""
    test = ""
    link = ""
    link_name = ""
    link_path = "services/"+service+"/html/link.html"
    with open(link_path, 'r') as content_file:
        link = content_file.read()
    link_a = link.split(" ", 1)
    link = link_a[0]
    link_name = link_a[1]
    client_path = "services/"+service+"/client/client.txt"
    with open(client_path, 'r') as content_file:
        client = content_file.read()
    client_a = client.split("\n")
    client = client_a[0]
    test_path = "services/"+service+"/client/"+client_a[1]
    with open(test_path, 'r') as content_file:
        test = content_file.read()
    return render_template("details.html",url=url,service=service,client=client,test=test,link=link,link_name=link_name)

@app.route('/robot.txt')
def robot():
    return render_template("robot.html")

if __name__ == '__main__':
    app.run(host="0.0.0.0")
