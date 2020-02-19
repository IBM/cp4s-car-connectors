

def get_json(response):
    try: return response.json()
    except: return {}

FAILURE = 0
IN_PROGRESS = 1
SUCCESS = 2

DB_FAILURE = 0
DB_READY = 1

class Status(dict):
    def __init__(self):
        self['status'] = FAILURE
        self['status_code'] = 0

    @property
    def status(self):
        return self['status']

    @status.setter
    def status(self, value):
        self['status'] = value

    @property
    def status_code(self):
        return self.get('status_code')

    @status_code.setter
    def status_code(self, value):
        self['status_code'] = value

    @property
    def error(self):
        return self.get('error')

    @error.setter
    def error(self, value):
        self['error'] = value

