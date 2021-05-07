import sqlite3

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def dict_factory(cursor, row):
    d = dotdict()
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


db = sqlite3.connect('mail.db')
db.row_factory = dict_factory


def init():
    db.execute("""
        CREATE TABLE IF NOT EXISTS mails (
            id INTEGER PRIMARY KEY,
            recieved_at,
            sender,
            reciever,
            subject,
            read,
            content
        );
    """)


init()


def select(query, args={}):
    cur = db.cursor()
    cur.execute(query, args)
    return cur.fetchall()


def first(query, args={}):
    cur = db.cursor()
    cur.execute(query, args)
    return cur.fetchone()


def execute(query, args={}):
    cur = db.cursor()
    cur.execute(query, args)
    db.commit()


def commit():
    db.commit()
