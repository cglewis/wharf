import MySQLdb as mdb

HOST="localhost"
PORT=49159
USER="admin"
PW="mysql-server"
DB="test"
m_server = mdb.connect(host=HOST, port=PORT, user=USER, passwd=PW, db=DB)
print "connected successfully"

