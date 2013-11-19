from flask import Flask
from flask import Markup
from flask import render_template
from flask import request
from flask import jsonify
from functools import wraps
from flask import request, Response

from docker import client

from os import environ
from os import listdir
from os import path

import redis
import time

app = Flask(__name__)
app.debug = True

#set defaults

#IMAGE_NAME = "damien/mongodb"
DOMAIN = "localhost"
HIPACHE_PORT="80"
REDIS_HOST="localhost"
REDIS_PORT=6379
DOCKER_HOST="localhost"

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

r = redis.StrictRedis(host=REDIS_HOST, port=int(REDIS_PORT))
c = client.Client(version="1.6", base_url='http://%s:4243' % DOCKER_HOST)

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret' 

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@requires_auth
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
@requires_auth
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

@app.route('/new/<service>', methods=["POST"])
@requires_auth
def new(service):
    exposed_ports = []
    # !! TODO try/expect
    dockerfile = "services/"+service+"/docker/Dockerfile"
    with open(dockerfile, 'r') as content_file:
        for line in content_file:
            if line.startswith("EXPOSE"):
                line = line.strip()
                line_a = line.split(" ")
                for port in line_a[1:]:
                    exposed_ports.append(port)
    container = []
    try:
        image_id = "JUNK"
        image_id_path = "services/"+service+"/.image_id"
        with open(image_id_path, 'r') as content_file:
            image_id = content_file.read()
        container = c.create_container(image_id, ports=exposed_ports)
    except:
        image_id, response = c.build(path="services/"+service+"/docker/", tag=service)
        image_id_path = "services/"+service+"/.image_id"
        with open(image_id_path, 'w') as content_file:
            content_file.write(image_id)
        container = c.create_container(image_id, ports=exposed_ports)
    container_id = container["Id"]
    #bindings = {}
    #for exposed_port in exposed_ports:
    #    port = exposed_port+"/tcp"
    #    bindings[port] = [{'HostIp': '', 'HostPort': ''}]
    #c.start(container_id, port_bindings=bindings)
    c.start(container_id)
    for exposed_port in exposed_ports:
        container_port = c.port(container_id, exposed_port)
        r.rpush("frontend:%s.%s" % (container_id, DOMAIN), container_id)
        r.rpush("frontend:%s.%s" % (container_id, DOMAIN), "http://%s:%s" %(DOMAIN, container_port))
        # !! TODO more than one url when there is more than one exposed_port
        if HIPACHE_PORT == "80":
            url = "%s:%s" % (DOMAIN, container_port)
        else:
            url="%s:%s" % (DOMAIN, container_port)

    return jsonify(url=url)

@app.route('/details/<service>/<url>')
@requires_auth
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
    return render_template("details.html",
                           url=url,
                           service=service,
                           client=client,
                           test=test,
                           link=link,
                           link_name=link_name)

@app.route('/robot.txt')
@requires_auth
def robot():
    return render_template("robot.html")

if __name__ == '__main__':
    app.run(host="0.0.0.0")
