from flask import Flask
from flask import Markup
from flask import Response
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask.ext.babel import Babel
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security
from flask.ext.security import SQLAlchemyUserDatastore
from flask.ext.security import UserMixin
from flask.ext.security import RoleMixin
from functools import wraps
from werkzeug import secure_filename

from docker import client
from sh import git
from sh import mv

from os import environ
from os import listdir
from os import path
from os import remove
from os import rmdir

import redis
import tarfile
import time
import zipfile

#set defaults

DOMAIN = "localhost"
HIPACHE_PORT="80"
REDIS_HOST="localhost"
REDIS_PORT=6379
DOCKER_HOST="localhost"
ALLOWED_EXTENSIONS = set(['gz', 'zip'])
UPLOAD_FOLDER = '/home/vagrant/wharf/tmp/'
SERVICES_FOLDER = '/home/vagrant/wharf/services/'
SERVICE_DICT = {'description':'description.txt',
                'client':'client/client.txt',
                'about':'html/about.html',
                'body':'html/body.html',
                'link':'html/link.html',
                'dockerfile':'docker/Dockerfile'}

# environment variables, must be set in order for application to function
#try:
#    DOMAIN=environ["DOMAIN"]
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

app = Flask(__name__)
app.config['DEBUG'] = True
# this should be re-generated for production use
app.config['SECRET_KEY'] = 'EckNi2Fluincawd+'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/db.sqlite'
app.config['DEFAULT_MAIL_SENDER'] = 'dockerwharf@gmail.com'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
# this should be re-generated for production use
app.config['SECURITY_PASSWORD_SALT'] = 'S)1<P3_~$XF}DI=#'
app.config['SECURITY_POST_REGISTER_VIEW'] = '/login'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SERVICES_FOLDER'] = SERVICES_FOLDER
app.config.from_object('config.email')
app.debug = True

# Setup mail extension
mail = Mail(app)

# Setup babel
babel = Babel(app)

# Create database connection object
db = SQLAlchemy(app)

@babel.localeselector
def get_locale():
    override = request.args.get('lang')

    if override:
        session['lang'] = override

    rv = session.get('lang', 'en')
    return rv

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return '<User id=%s email=%s>' % (self.id, self.email)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

db.create_all()

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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
@requires_auth
def index():
    if request.method == 'POST':
        url = ""
        file = ""
        try:
            url = request.form['wharf_url']
        except:
            url = ""
        try:
            file = request.files['file']
        except:
            file = ""
        if file != "":
            try:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(path.join(app.config['UPLOAD_FOLDER'], filename))
                    if filename.rsplit('.', 1)[1] == "zip":
                        with zipfile.ZipFile(path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as service_zip:
                            service_zip.extractall(path.join(app.config['UPLOAD_FOLDER'],
                                                             filename.rsplit('.', 1)[0]))
                            # !! TODO
                            #    allow exception for dockerfile, check at root as well
                            # check for existence of necessary files
                            for key,value in SERVICE_DICT.items():
                                if not path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                             filename.rsplit('.', 1)[0],
                                                             filename.rsplit('.', 1)[0],
                                                             value)):
                                    # !! TODO make this better
                                    #         render a form to fill out the missing metadata
                                    return render_template("failed.html")
                            # move to services folder
                            i = 0
                            while i != -1:
                                try:
                                    if i == 0:
                                        mv(path.join(app.config['UPLOAD_FOLDER'], 
                                                     filename.rsplit('.', 1)[0], 
                                                     filename.rsplit('.', 1)[0]),
                                           app.config['SERVICES_FOLDER'])
                                    elif i == 1:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 1)[0], 
                                                     filename.rsplit('.', 1)[0]), 
                                           path.join(app.config['UPLOAD_FOLDER'], 
                                                     filename.rsplit('.', 1)[0], 
                                                     (filename.rsplit('.', 1)[0])+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'], 
                                                     filename.rsplit('.', 1)[0], 
                                                     (filename.rsplit('.', 1)[0])+str(i)), 
                                           app.config['SERVICES_FOLDER'])
                                    else:
                                        mv(path.join(app.config['UPLOAD_FOLDER'], 
                                                     filename.rsplit('.', 1)[0], 
                                                     (filename.rsplit('.', 1)[0])+str(i-1)), 
                                           path.join(app.config['UPLOAD_FOLDER'], 
                                                     filename.rsplit('.', 1)[0], 
                                                     (filename.rsplit('.', 1)[0])+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'], 
                                                     filename.rsplit('.', 1)[0], 
                                                     (filename.rsplit('.', 1)[0])+str(i)), 
                                           app.config['SERVICES_FOLDER'])
                                    i = -1
                                except:
                                    i += 1
                            # remove leftover files in tmp
                            remove(path.join(app.config['UPLOAD_FOLDER'], filename))
                            rmdir(path.join(app.config['UPLOAD_FOLDER'], filename.rsplit('.', 1)[0]))

                    elif filename.rsplit('.', 1)[1] == "gz":
                        with tarfile.open(path.join(app.config['UPLOAD_FOLDER'], filename)) as service_gz:
                            service_gz.extractall(path.join(app.config['UPLOAD_FOLDER'],
                                                            filename.rsplit('.', 2)[0]))
                            # !! TODO
                            #    allow exception for dockerfile, check at root as well
                            # check for existence of necessary files
                            for key,value in SERVICE_DICT.items():
                                if not path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                             filename.rsplit('.', 2)[0],
                                                             filename.rsplit('.', 2)[0],
                                                             value)):
                                    # !! TODO make this better
                                    #         render a form to fill out the missing metadata
                                    return render_template("failed.html")
                            # move to services folder
                            i = 0
                            while i != -1:
                                try:
                                    if i == 0:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 2)[0],
                                                     filename.rsplit('.', 2)[0]),
                                           app.config['SERVICES_FOLDER'])
                                    elif i == 1:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 2)[0], 
                                                     filename.rsplit('.', 2)[0]), 
                                           path.join(app.config['UPLOAD_FOLDER'], 
                                                     filename.rsplit('.', 2)[0], 
                                                     (filename.rsplit('.', 2)[0])+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 2)[0], 
                                                     (filename.rsplit('.', 2)[0])+str(i)), 
                                           app.config['SERVICES_FOLDER'])
                                    else:
                                        mv(path.join(app.config['UPLOAD_FOLDER'], 
                                                     filename.rsplit('.', 2)[0], 
                                                     (filename.rsplit('.', 2)[0])+str(i-1)), 
                                           path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 2)[0], 
                                                     (filename.rsplit('.', 2)[0])+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'], 
                                                     filename.rsplit('.', 2)[0], 
                                                     (filename.rsplit('.', 2)[0])+str(i)), 
                                           app.config['SERVICES_FOLDER'])
                                    i = -1
                                except:
                                    i += 1
                            # remove leftover files in tmp
                            remove(path.join(app.config['UPLOAD_FOLDER'], filename))
                            rmdir(path.join(app.config['UPLOAD_FOLDER'], filename.rsplit('.', 2)[0]))
                    else:
                        return render_template("failed.html")
                    # !! TODO
                    #    some post-processing once the file is uploaded
                else:
                    return render_template("failed.html")
            except:
                print "No file selected"
        elif url != "":
            try:
                # !! TODO
                if url:
                    # !! TODO try/except
                    if url.rsplit('.', 1)[1] == "git":
                        # !! TODO try/except - if the folder already exists
                        git.clone(url, path.join(app.config['UPLOAD_FOLDER'],
                                                 (url.rsplit('/', 1)[1]).rsplit('.', 1)[0]))
                        # !! TODO
                        #    allow exception for dockerfile, check at root as well
                        for key,value in SERVICE_DICT.items():
                            if not path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                         (url.rsplit('/', 1)[1]).rsplit('.', 1)[0], value)):
                                # !! TODO make this better
                                #         render a form to fill out the missing metadata
                                print path.join(app.config['UPLOAD_FOLDER'],
                                                (url.rsplit('/', 1)[1]).rsplit('.', 1)[0], value),"failed",value
                                return render_template("failed.html")
                            else:
                                print "found",value
                        # !! TODO check for metadata files
                        # !! TODO check if the service already exists
                        # move to services folder
                        # !! TODO needs to be fixed
                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                     (url.rsplit('/', 1)[1]).rsplit('.', 1)[0]), 
                           path.join(app.config['SERVICES_FOLDER'],
                                     (url.rsplit('/', 1)[1]).rsplit('.', 1)[0])) 
                        # !! TODO build in the background
                    else:
                        print url
            except:
                print "Bad URL"
        else:
            return render_template("failed.html")
        return redirect(url_for('index'))

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
        # !! TODO try/except
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
    # !! TODO try/except
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
