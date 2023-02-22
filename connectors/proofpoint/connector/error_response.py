"""Generic Error Mappings for API requests."""

from enum import Enum
import traceback
import importlib
import os
import json


class ErrorCode(Enum):
    """Error codes mappings"""
    # existing generic errors mapped
    TRANSMISSION_UNKNOWN = 'unknown'
    TRANSMISSION_CONNECT = 'service_unavailable'


class ErrorResponder:

    @staticmethod
    def fill_error(return_object, message_structure=None, status_code=None):
        """ Construct the API response error response
            params: dict, error_response, status_code
            return: dict """
        return_object['success'] = False
        error_code = ErrorCode.TRANSMISSION_UNKNOWN

        # Checks error message is string or json or class object
        if "error_response" in message_structure.__dir__():
            structure_map = message_structure.error_response
        elif 'args' in message_structure.__dir__():
            structure_map = message_structure.args[0]
        else:
            structure_map = message_structure
            error_code = status_code
            error_msg = message_structure.decode('utf-8', errors='ignore')

            if ErrorResponder.is_plain_string(error_msg):
                structure_map = error_msg
            elif ErrorResponder.is_json_string(error_msg):
                structure_map = json.loads(error_msg)
                structure_map = structure_map.get('message', None)

        if structure_map:
            return_object['error'] = str(structure_map)
        ErrorMapperBase.set_error_code(return_object, error_code)

        # If error message is class object then particular connector error mapper file is used
        if hasattr(message_structure, '__dict__'):
            ErrorResponder.call_module_error_mapper(message_structure, return_object)
        return return_object

    @staticmethod
    def call_module_error_mapper(json_data, return_object):  # pragma: no cover
        """ Map the error with connectors error code """
        caller_path_list = traceback.extract_stack()[-3].filename.split(os.path.sep)
        path_start_position = ErrorResponder.r_index(caller_path_list, 'connector')
        module_path = '.'.join(caller_path_list[path_start_position: -1]) + '.'
        try:
            module = importlib.import_module(module_path)
            if json_data is not None:
                module.ErrorMapper.set_error_code(json_data, return_object)
            else:
                ErrorMapperBase.set_error_code(return_object, module.ErrorMapper.DEFAULT_ERROR)
        except ModuleNotFoundError:
            pass

    @staticmethod
    def r_index(my_list, my_value):
        """ Return the current connector file name """
        return len(my_list) - my_list[::-1].index(my_value) - 1

    @staticmethod
    def is_plain_string(s):
        """ Checks value is string or not """
        return isinstance(s, str) and not s.startswith('<?') and not s.startswith('{')

    @staticmethod
    def is_json_string(s):
        """ Checks value is json string or not """
        return isinstance(s, str) and s.startswith('{')


class ErrorMapperBase:
    @staticmethod
    def set_error_code(return_obj, code, message=None):
        """ Map the error code """
        if isinstance(code, Enum):
            return_obj['code'] = code.value
        else:
            return_obj['code'] = code
        if message is not None:
            return_obj['error'] = message

        return return_obj
