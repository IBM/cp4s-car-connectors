import requests
import json
import sys
from connector.error_response import ErrorResponder
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, ConnectTimeout
from datetime import datetime, timedelta
from car_framework.context import context
from car_framework.util import ErrorCode


class AssetServer(object):

    def __init__(self):

        # Get server connection arguments from config file
        with open('connector/proofpoint_config.json', 'rb') as json_data:
            self.config = json.load(json_data)
        self.basic_auth = HTTPBasicAuth(context().args.username,
                                        context().args.password)

    # Pulls asset data for all collection entities
    def get_collection(self, asset_server_endpoint):
        """
        Fetch the datas from api.
        parameters:
            asset_server_endpoint(str): api end point
        returns:
            json_data(dict): Api response
        """
        return_obj = {}
        try:
            resp = requests.get('%s/%s' % (context().args.server, asset_server_endpoint),
                                auth=self.basic_auth, headers=self.config['parameter']['headers'])
            if resp.status_code != 200:
                ErrorResponder.fill_error(return_obj, resp.content, resp.status_code)
                # This exception handled in full import for time range beyond 7 days.
                if "The requested start time is too far into the past" in resp.text:
                    raise Exception(return_obj)
        except (ConnectionError, ConnectTimeout) as ex:
            # Catching requests general exceptions
            ErrorResponder.fill_error(return_obj, ex)
        if return_obj:
            context().logger.error("ProofPoint API returned error, error details : %s", return_obj)
            sys.exit(ErrorCode.DATASOURCE_FAILURE_DEFAULT.value)
        return resp.json()

    def get_model_state_delta(self, last_model_state_id, new_model_state_id):
        """
        Fetch the records from two api's.
        parameters:
            last_model_state_id(str): last modified time
            new_model_state_id(str):  current time
        returns:
            delta(dict): Api response
        """

        siem_api_collection = self.get_siem_api(last_model_state_id)

        people_api_input = "%s?window=%s" % (self.config['endpoint']['people'],
                                             self.config['parameter']['time_window'])

        people_api_collection = self.get_collection(people_api_input)

        delta = {'siem': siem_api_collection, 'people': people_api_collection['users']}

        return delta

    def get_siem_api(self, start_time):
        """
        Fetch the threats for SIEM api.
        parameters:
            start_time(str): from which date need to fetch
        returns:
            collection(list): SIEM api response
        """

        start_time = self.epoch_to_datetime_conv(start_time)
        start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        collection = []
        current_time = datetime.utcnow()

        while start_time < current_time:
            next_hour = start_time + timedelta(hours=1)

            if next_hour > current_time:
                next_hour = current_time
                # ProofPoint SIEM API accepts minimum time interval 30 sec
                if (next_hour - start_time) <= timedelta(seconds=30):
                    context().logger.info('interval time provided: %s' % (next_hour - start_time))
                    return collection

            end_point = "%s?format=%s&interval=%s/%s" % (self.config['endpoint']['siem'],
                                                         self.config['parameter']['format'],
                                                         start_time.strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                                                         next_hour.strftime('%Y-%m-%dT%H:%M:%S') + 'Z')
            events = self.get_collection(end_point)

            data = {'clicks': events['clicksBlocked'] + events["clicksPermitted"],
                    'events': events['messagesDelivered'] + events['messagesBlocked']}

            collection.append(data)

            start_time = next_hour

        return collection

    def epoch_to_datetime_conv(self, epoch_time):
        """
        Convert epoch time to date format time
        :param epoch_time: time in epoch
        :return: date format utc time
        """
        epoch_time = float(epoch_time) / 1000.0
        datetime_time = datetime.fromtimestamp(epoch_time)
        utc_format_string = "{date_part}T{time_part}Z"
        utc_list = str(datetime_time).split()
        return utc_format_string.format(date_part=utc_list[0], time_part=utc_list[1])
