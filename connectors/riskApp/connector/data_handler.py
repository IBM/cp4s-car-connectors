import datetime
import ipaddress

from car_framework.context import context

import uuid

# maps drm-server endpoints to CAR service endpoints
endpoint_mapping = \
    {'AssetRetention': 'application','AssetDSList': 'ipaddress','AssetUsage':'businessprocess'}

def get_report_time():
    delta = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)
    milliseconds = delta.total_seconds() * 1000
    return milliseconds


class DataHandler(object):

    def __init__(self, xrefproperties):
        self.edges= {'DSAPPLICATION':'application_ipaddress','ApplicationBPMapping': 'businessprocess_application'}
        self.xrefproperties = xrefproperties
        now = get_report_time()
        self.source = {'_key': context().args.source, 'name': context().args.tenantUrl, 'description': 'IBM Security Verify tenant for DRM server'}
        self.report = {'_key': str(now), 'timestamp' : now, 'type': 'Reference DRM server', 'description': 'Reference DRM server'}
        self.source_report = [{'active': True, '_from': 'source/' + self.source['_key'], '_to': 'report/' + self.report['_key'], 'timestamp': self.report['timestamp']}]

    def copy_fields(self, obj, *fields):
        res = {}
        for field in fields:
            res[field] = obj[field]
        return res

    def add_edge(self, name, object):
        objects = self.edges.get(name)
        if not objects:
            objects = []; self.edges[name] = objects
        objects.append(object)

    # Create application Object as per CAR data model from data source
    def handle_AssetRetention(self, obj):
        res = {}
        try:
            check_keys = {'id', 'name', 'description', 'conceptProperties',"isDeleted"}
            res_obj = {}
            if (check_keys.issubset(obj.keys())):
                res['external_id'] = str(obj['id'])
                res_obj['name'] = str(obj['name'])
                res_obj['description'] = str(obj['description'])
                if obj['isDeleted'] == 1:
                    res_obj['_deleted'] = int(datetime.datetime.now().timestamp()*1000)
                for item_property in obj['conceptProperties']:
                    if item_property['value'] is None:
                        item_property['value'] = ''
                    if item_property['category'] is None:
                        item_property['category'] = ''
                    res_obj[str(item_property['propertyName'])] = str(
                        item_property['value'] + " ~ " + str(item_property['category']))
                res.update(res_obj)
                del res_obj
            else:
                raise KeyError("Not all the keys present in the data...")
        except Exception as e:
            raise Exception("Exception in parsing the data:")
        return res

    # Create ipaddress Object as per CAR data model from data source
    def handle_AssetDSList(self, obj):
        res = {}
        try:
            ipaddress.ip_address(obj['entityValue'])
        except ValueError:
            return
        if obj['entityValue'] != "":
            try:
                check_keys = {'entityValue','name', 'description', 'conceptProperties'}
                res_obj={}
                if(check_keys.issubset(obj.keys())):
                    res['_key'] = str(obj['entityValue'])
                    if obj['isDeleted'] == 1:
                        res_obj['_deleted'] = int(datetime.datetime.now().timestamp() * 1000)
                    res_obj['name'] = str(obj['entityValue'])
                    res_obj['description'] = str(obj['description'])
                    for item_property in obj['conceptProperties']:
                        if item_property['value'] is None:
                            item_property['value'] = ''
                        if item_property['category'] is None:
                            item_property['category'] = ''
                        res_obj[str(item_property['propertyName'])] = str(
                            item_property['value'] + " ~ " + str(item_property['category']))
                    res.update(res_obj)
                    del res_obj
                else:
                    raise KeyError("Not all the keys present in the data...")
            except Exception as e:
                raise Exception("Exception in parsing the data:")
            return res

    # Create BusinessProcess Object as per CAR data model from data source
    def handle_AssetUsage(self, obj):
        res = {}
        try:
            check_keys = {'id', 'name', 'description', 'conceptProperties'}
            res_obj = {}
            if (check_keys.issubset(obj.keys())):
                res['external_id'] = str(obj['id'])
                res_obj['name'] = str(obj['name'])
                res_obj['description'] = str(obj['description'])
                if obj['isDeleted'] == 1:
                    res_obj['_deleted'] = int(datetime.datetime.now().timestamp()*1000)
                for item_property in obj['conceptProperties']:
                    if item_property['value'] is None:
                        item_property['value'] = ''
                    if item_property['category'] is None:
                        item_property['category'] = ''
                    res_obj[str(item_property['propertyName'])] = str(
                        item_property['value'] + " ~ " + str(item_property['category']))
                res.update(res_obj)
                del res_obj
            else:
                raise KeyError("Not all the keys present in the data...")
        except Exception as e:
            raise Exception("Exception in parsing the data:")
        return res

    # Create application_ipaddress Object as per CAR data model from data source
    def handle_DSAPPLICATION(self, obj):
        res = dict()
        try:
            if obj['ipAddress'] != "":
                res['_from_external_id'] = str(obj['childConceptId'])
                res['_to'] = 'ipaddress/' + obj['ipAddress']
                res['timestamp'] = float(obj['lastUpdate'])
                res['report'] = self.report['_key']
                res['source'] = context().args.source
                res['active'] = True
        except Exception as e:
            raise Exception("Exception in parsing the data:")
        return res

    # Create businessprocess_application Object as per CAR data model from data source
    def handle_ApplicationBPMapping(self, obj):
        res = dict()
        try:
            res['external_id'] = str(uuid.uuid4())
            res['_from_external_id'] = str(obj['childConcept']['id'])
            res['_to_external_id'] = str(obj['parentId'])
            res['timestamp'] = float(obj['lastUpdate'])
            res['report'] = self.report['_key']
            res['source'] = context().args.source
            res['active'] = True
        except Exception as e:
            raise Exception("Exception in parsing the data:")
        return res
