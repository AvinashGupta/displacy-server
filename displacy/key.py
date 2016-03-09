import time

import boto.dynamodb


class Key(object):
    def __init__(self, **kwargs):
        self.access_key_id = kwargs.pop('access_key_id')
        self.secret_access_key = kwargs.pop('secret_access_key')
        self.region = kwargs.pop('region')
        self.table_name = kwargs.pop('table')

        self.conn = boto.dynamodb.connect_to_region(self.region,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key)
        self.table = self.conn.get_table(self.table_name)

    def __setitem__(self, key, value):
        attrs = {
            'value': value,
            'created_at': int(time.time())
        }

        item = self.table.new_item(hash_key=int(key), attrs=attrs)
        item.put()

    def get(self, key):
        try:
            return self.table.get_item(hash_key=int(key))['value']
        except boto.dynamodb.exceptions.DynamoDBKeyNotFoundError:
            return None

    def status(self):
        try:
            self.table.scan(request_limit=1).next_response()
            return True
        except Exception:
            return False
