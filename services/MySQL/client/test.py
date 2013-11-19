import MySQLdb as mdb

HOST="localhost"
PORT=49158
USER="admin"
PW="mysql-server"
DB="mysql"
m_server = mdb.connect(host=HOST, port=PORT, user=USER, passwd=PW, db=DB)
print "connected successfully"

