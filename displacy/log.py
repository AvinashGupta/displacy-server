import time
import uuid

import boto.dynamodb


class Log(object):
    def __init__(self, **kwargs):
        self.access_key_id = kwargs.pop('access_key_id')
        self.secret_access_key = kwargs.pop('secret_access_key')
        self.region = kwargs.pop('region')
        self.table_name = kwargs.pop('table')

        self.conn = boto.dynamodb.connect_to_region(self.region,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key)
        self.table = self.conn.get_table(self.table_name)

    def create(self, request):
        attrs = {
            'path': request.path,
            'text': request.json['text'],
            'user_agent': request.user_agent.string,
            'remote_addr': request.access_route[0],  # support x-forwarded-for header
            'created_at': int(time.time())
        }

        item = self.table.new_item(
            hash_key=uuid.uuid1().hex,
            attrs=attrs)

        item.put()

    def status(self):
        try:
            self.table.scan(request_limit=1).next_response()
            return True
        except Exception:
            return False
