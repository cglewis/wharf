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

from os import environ
from os import listdir
from os import path

import redis
import tarfile
import time
import zipfile

ALLOWED_EXTENSIONS = set(['gz', 'zip'])
UPLOAD_FOLDER = '/home/vagrant/wharf/tmp/'

app = Flask(__name__)
app.config['DEBUG'] = True
# this should re-generated for production use
app.config['SECRET_KEY'] = 'EckNi2Fluincawd+'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/db.sqlite'
app.config['DEFAULT_MAIL_SENDER'] = 'dockerwharf@gmail.com'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
# this should re-generated for production use
app.config['SECURITY_PASSWORD_SALT'] = 'S)1<P3_~$XF}DI=#'
app.config['SECURITY_POST_REGISTER_VIEW'] = '/login'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_object('config.email')
app.debug = True

# Setup mail extension
mail = Mail(app)

# Setup babel
babel = Babel(app)

#set defaults

DOMAIN = "localhost"
HIPACHE_PORT="80"
REDIS_HOST="localhost"
REDIS_PORT=6379
DOCKER_HOST="localhost"

#environment variables, must be set in order for application to function
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

@babel.localeselector
def get_locale():
    override = request.args.get('lang')

    if override:
        session['lang'] = override

    rv = session.get('lang', 'en')
    return rv

# Create database connection object
db = SQLAlchemy(app)

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
def index():
    if request.method == 'POST':
        try:
            # !! TODO
            #    process url if that was entered instead
            #url = request.form['wharf_url']
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(path.join(app.config['UPLOAD_FOLDER'], filename))
                # !! TODO
                #    some post-processing once the file is uploaded
                if filename.rsplit('.', 1)[1] == "zip":
                    with zipfile.ZipFile(path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as service_zip:
                        service_zip.extractall(path.join(app.config['UPLOAD_FOLDER'], filename.rsplit('.', 1)[0])) 
                # !! TODO
                #    elif tarfile
        except:
            print "No file selected"
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
