from wharf import app

from flask import jsonify
from flask.ext.login import current_user

from docker import client

from os import path

import datetime
import json
import redis

HIPACHE_PORT="80"
DOCKER_HOST="localhost"

r = redis.StrictRedis(host=app.config['REDIS_HOST'], port=int(app.config['REDIS_PORT']))
c = client.Client(version="1.6", base_url='http://%s:4243' % DOCKER_HOST)

@app.route('/new/<service>', methods=["POST"])
def new(service):
    exposed_ports = []
    # !! TODO try/expect
    dockerfile = ""
    docker_path = ""
    if path.exists(path.join(app.config['SERVICES_FOLDER'],
                             service,
                             app.config['SERVICE_DICT']['dockerfile'])):
        dockerfile = "services/"+service+"/"+app.config['SERVICE_DICT']['dockerfile']
        docker_path = "services/"+service+"/docker/"
    elif path.exists(path.join(app.config['SERVICES_FOLDER'],
                             service,
                             "Dockerfile")):
        dockerfile = "services/"+service+"/Dockerfile"
        docker_path = "services/"+service+"/"
    # if dockerfile is still ""
    # docker index
    else:
        # !! TODO try/except
        service = service.replace("-", "/", 1)
        c.pull(service)
        container = c.create_container(service)
        container_id = container["Id"]
        c.start(container)
        b = c.inspect_container(container)
        ports = b['NetworkSettings']['PortMapping']['Tcp']
        for key,value in ports.items():
            exposed_ports.append(key)
        for exposed_port in exposed_ports:
            container_port = c.port(container_id, exposed_port)
            r.rpush("frontend:%s.%s" % (container_id, app.config['DOMAIN']), container_id)
            r.rpush("frontend:%s.%s" % (container_id, app.config['DOMAIN']), "http://%s:%s" %(app.config['DOMAIN'], container_port))
            # !! TODO more than one url when there is more than one exposed_port
            if HIPACHE_PORT == "80":
                url = "%s:%s" % (app.config['DOMAIN'], container_port)
            else:
                url = "%s:%s" % (app.config['DOMAIN'], container_port)
        today = datetime.datetime.now()
        today_str = '{0.year}-{0.month:02d}-{0.day:02d} {0.hour:02d}:{0.minute:02d}:{0.second:02d}.{0.microsecond:06d}'.format(today)
        hmap = {}
        hmap['service'] = service
        hmap['timestamp'] = today_str
        hmap['owned_by'] = current_user.email
        r.hmset(url, hmap)
        r.rpush(current_user.email, url)
        return jsonify(url=url)

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
        # !! TODO try/except
        image_id, response = c.build(path=docker_path, tag=service)
        # !! TODO leaving in for debugging for now
        print image_id, response
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
        r.rpush("frontend:%s.%s" % (container_id, app.config['DOMAIN']), container_id)
        r.rpush("frontend:%s.%s" % (container_id, app.config['DOMAIN']), "http://%s:%s" %(app.config['DOMAIN'], container_port))
        # !! TODO more than one url when there is more than one exposed_port
        if HIPACHE_PORT == "80":
            url = "%s:%s" % (app.config['DOMAIN'], container_port)
        else:
            url = "%s:%s" % (app.config['DOMAIN'], container_port)

    today = datetime.datetime.now()
    today_str = '{0.year}-{0.month:02d}-{0.day:02d} {0.hour:02d}:{0.minute:02d}:{0.second:02d}.{0.microsecond:06d}'.format(today)
    hmap = {}
    hmap['service'] = service
    hmap['timestamp'] = today_str
    hmap['owned_by'] = current_user.email
    r.hmset(url, hmap)
    r.rpush(current_user.email, url)
    return jsonify(url=url)
