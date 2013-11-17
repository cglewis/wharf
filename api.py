from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify

#from docker import client

from os import environ

#import redis

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
    return render_template("index.html")

@app.route('/saas/<service>')
def saas(service):
    about = ""
    body = ""
    links = ""
    about_path = "services/"+service+"/html/about.html"
    with open(about_path, 'r') as content_file:
        about = content_file.read()
    body_path = "services/"+service+"/html/body.html"
    with open(body_path, 'r') as content_file:
        body = content_file.read()
    links_path = "services/"+service+"/html/links.html"
    with open(links_path, 'r') as content_file:
        links = content_file.read()
    return render_template("saas.html",service=service,about=about,body=body,links=links)

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
    return render_template("details.html",url=url,service=service)

@app.route('/robot.txt')
def robot():
    return render_template("robot.html")

if __name__ == '__main__':
    app.run(host="0.0.0.0")
