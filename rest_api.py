#!/usr/bin/env python
from __future__ import unicode_literals
from __future__ import print_function
import sys

import falcon
import json
from os import path

from displacy.handlers import handle_parse, handle_manual


try:
  unicode
except NameError:
  unicode = str


class Endpoint(object):
    def __init__(self, make_model):
        self.make_model = make_model

    def set_header(self, resp):
        resp.content_type = 'text/string'
        resp.append_header('Access-Control-Allow-Origin', "*")
        resp.status = falcon.HTTP_200

    def set_body(self, resp, parse):
        resp.body = json.dumps(parse.to_json(), indent=4)

    def on_get(self, req, resp, text="", actions=""):
        if not isinstance(text, unicode):
            text = text.decode('utf8')
        self.set_body(resp, self.make_model({"text": text, "actions": actions}))
        self.set_header(resp)

    def on_post(self, req, resp, text="", actions=""):
        body_bytes = req.stream.read()
        json_data = json.loads(body_bytes.decode('utf8'))
        self.set_body(resp, self.make_model(json_data))
        self.set_header(resp)


class ServeLoad(Endpoint):
    def on_get(self, req, resp, key='0'):
        global db
        parse = db.get(int(key), {})
        self.set_body(resp, parse)
        self.set_header(resp)


class ParseDB(object):
    def __init__(self, loc):
        create_table = not os.path.exists(loc)
        self.conn = sqlite3.connect(loc)
        self.cursor = self.conn.cursor()
        if create_table:
            self.cursor.execute('''CREATE TABLE parses (id INTEGER PRIMARY KEY, parse TEXT)''')
            self.conn.commit()

    def get(self, key):
        print("Get", repr(key))
        result = self.cursor.execute('SELECT * FROM parses WHERE id=?', (int(key),))
        return result.fetchone()

    def set(self, key, value):
        print("Set", key, value)
        self.cursor.execute("INSERT OR IGNORE INTO parses VALUES (?, ?)", (key, value))
        self.conn.commit()

    def save(self, parse):
        key = abs(hash(json.dumps(parse)))

    def load(self, key):
        try:
            key = int(key)
        except ValueError:
            return None
        return self.get(key)


def handle_save(parse):
    string = json.dumps(parse)
    key = abs(hash(string))
    db[key] = parse
    return key


db = sqlitedict.SqliteDict('tmp.db', autocommit=True)
app = falcon.API()

app.add_route('/api/displacy/parse/', Endpoint(handle_parse))
app.add_route('/api/displacy/manual/', Endpoint(handle_manual))
app.add_route('/api/displacy/save/', Endpoint(handle_save))
app.add_route('/api/displacy/load/{key}', ServeLoad(lambda json_data: json_data))


if __name__ == '__main__':
    from wsgiref import simple_server
    httpd = simple_server.make_server('0.0.0.0', 80, app)
    httpd.serve_forever()
