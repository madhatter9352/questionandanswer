from flask import g
import sqlite3


def connect_db():
    sql = sqlite3.connect("/home/lazaro/Documentos/DBSQLITE/questandanswr.db", timeout=10)
    sql.row_factory = sqlite3.Row
    return sql


def get_bd():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db
