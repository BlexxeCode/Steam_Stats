from app import app
from flaskext.mysql import MySQL

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password@12'
app.config['MYSQL_DATABASE_DB'] = 'steam'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)