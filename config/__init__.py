# PyMySQL as MySQLdb for Django on shared hosting (Timeweb)
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    pass
