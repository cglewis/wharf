from wharf import app

from flask import jsonify

from docker import client

from os import path

import redis

DOMAIN = "localhost"
HIPACHE_PORT="80"
DOCKER_HOST="localhost"
REDIS_HOST="localhost"
REDIS_PORT=6379
SERVICE_DICT = {'description':'description.txt',
                'client':'client/client.txt',
                'about':'html/about.html',
                'body':'html/body.html',
                'link':'html/link.html',
                'dockerfile':'docker/Dockerfile'}

r = redis.StrictRedis(host=REDIS_HOST, port=int(REDIS_PORT))
c = client.Client(version="1.6", base_url='http://%s:4243' % DOCKER_HOST)

@app.route('/new/<service>', methods=["POST"])
def new(service):
    exposed_ports = []
    # !! TODO try/expect
    dockerfile = ""
    docker_path = ""
    if path.exists(path.join(app.config['SERVICES_FOLDER'],
                             service,
                             SERVICE_DICT['dockerfile'])):
        dockerfile = "services/"+service+"/"+SERVICE_DICT['dockerfile']
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
            r.rpush("frontend:%s.%s" % (container_id, DOMAIN), container_id)
            r.rpush("frontend:%s.%s" % (container_id, DOMAIN), "http://%s:%s" %(DOMAIN, container_port))
            # !! TODO more than one url when there is more than one exposed_port
            if HIPACHE_PORT == "80":
                url = "%s:%s" % (DOMAIN, container_port)
            else:
                url = "%s:%s" % (DOMAIN, container_port)
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
        r.rpush("frontend:%s.%s" % (container_id, DOMAIN), container_id)
        r.rpush("frontend:%s.%s" % (container_id, DOMAIN), "http://%s:%s" %(DOMAIN, container_port))
        # !! TODO more than one url when there is more than one exposed_port
        if HIPACHE_PORT == "80":
            url = "%s:%s" % (DOMAIN, container_port)
        else:
            url = "%s:%s" % (DOMAIN, container_port)

    return jsonify(url=url)
