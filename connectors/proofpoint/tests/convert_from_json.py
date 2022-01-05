import json
import os


class JsonResponse:
    """
     Summary conversion of json data to dictionary.
          """
    def __init__(self, response_code, filename):
        self.status_code = response_code
        self.filename = filename

    def json(self):
        """return mock api response"""
        cur_path = os.path.dirname(__file__)
        abs_file_path = cur_path + "/proofpoint_tests_log/" + self.filename
        with open(abs_file_path, "rb") as json_file:
            json_str = json_file.read()
            json_data = json.loads(json_str)
            return json_data
