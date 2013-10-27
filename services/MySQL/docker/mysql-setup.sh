#!/bin/sh

/usr/sbin/mysqld &
sleep 5

# sets the admin password to 'mysql-server' which is accessible from the outside
echo "GRANT ALL ON *.* TO admin@'%' IDENTIFIED BY 'mysql-server' WITH GRANT OPTION; FLUSH PRIVILEGES" | mysql -ppassword
