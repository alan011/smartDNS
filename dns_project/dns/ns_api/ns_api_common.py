from django.http      import HttpResponse
from dns.models       import BindNSRecord
from dns              import dns_settings
from .ns_api_auth     import NSClusterAuth

import json, requests, random

class APICaller(object):
    def post_caller(self, api_url, post_data=None, isjson=True):
        if isjson:
            try:
                r = requests.post(api_url, json = post_data)
            except:
                return "ERROR: host not reachable: {}.".format(api_url)
        else:
            try:
                r = requests.post(api_url, data = post_data)
            except:
                return "ERROR: host not reachable: {}.".format(api_url)

        if r.status_code == 200:
            # To check the data successfully returned by geniusalt_api.
            try:
                return_data = r.json()
            except ValueError:  #This means data returned is a normal string, which cannot be used with r.json().
                return r.text
            else:
                return return_data
        else:
            return "ERROR: api call returned with status_code: {}, with message: {}".format(str(r.status_code),r.text)

    def get_caller(self, api_url, auth=None):
        """
        arg 'auth' is a tuple: (user, passwd).
        """
        if auth:
            r = requests.get(api_url, auth=auth)
        else:
            r = requests.get(api_url)
        if r.status_code == 200:
            try:
                return_data = r.json()
            except ValueError:
                return r.text
            else:
                return return_data
        else:
            return "ERROR: api call returned with status_code: {}, with message: {}".format(str(r.status_code),r.text)


class NSApiCommon(object):
    """
    Some common methods for NS API.
    """
    def checkPostData(self, request, legal_field_list=None, field_require=True, decode_type='utf-8'):
        post_data   = json.loads(request.body.decode(decode_type))

        ### post_data must be a JSON dict
        if not isinstance(post_data, dict):
            return HttpResponse('ERROR: post data illegal.', status=400)

        ### Fields required check.
        if field_require:
            for field in legal_field_list:
                if field not in post_data:
                    return HttpResponse('ERROR: post data illegal: Some fields required not provide.', status=400)
        elif 'ns_token' not in post_data:
            return HttpResponse('ERROR: post data illegal: Some fields required not provide.', status=400)

        return post_data

    def checkObjExist(self, obj_match_dict, db_model):
        queryset = db_model.objects.filter(**obj_match_dict)
        if queryset.exists():
            return queryset
        else:
            return None

    def dataCheckInDetail(self, ret_data):
        for field in ret_data:
            if isinstance(ret_data[field], HttpResponse):  ### Means illegal post data found.
                return ret_data[field]
        return ret_data

    def getUnappliedResolv(self):
        return BindNSRecord.objects.filter(is_deleted=0, is_applied=0)

    def get(self, request):
        return HttpResponse('ERROR: BAD_REQUEST\n',status=400)

    def prepare_post(self, request, field_require=True):
        """
        This method is designed to do the common things for the 'post' method of all NS API.
        This method requires sub-class to define attribute 'legal_fields'.
        This method prodives an attribute 'response_data' for sub-class.
        """
        ### Prepare the response data.
        self.response_data = {'result':'SUCCESS', 'message':'','unapplied_resolv_count':self.getUnappliedResolv().count()}

        ### Simply check post field.
        post_data   = self.checkPostData(request, self.legal_fields, field_require=field_require)
        if isinstance(post_data, HttpResponse):   ### Means error occured.
            return post_data

        ### Authentication
        if not self.simpleAuth(post_data['ns_token'], request):
            return HttpResponse('ERROR: Authentication failed.', status=403)

        ### Check post data in detail.
        return self.dataCheckInDetail(post_data)

    def readdAnObject(self, obj, attr_dict):
        """
        This method is designed to re-add a deleted object in DB.
        When an object in DB is deleted, it's not really been deleted, Only the attribute 'is_deleted' has been set to int 1.
        When re-adding an object, 'is_deleted' and 'is_applied' will be set to 0, other attributes will be covered by new values posted from the Add API.
        """
        obj.is_deleted = 0
        for attr in attr_dict:
            setattr(obj, attr, attr_dict[attr])
        if hasattr(obj, 'is_applied'):
            setattr(obj, 'is_applied', 0)
        obj.save()

    def notice_slaves(self, notice):
        api_caller = APICaller()
        post_data  = {'ns_token':NSClusterAuth.simple_auth_string}
        ret_data = {}
        if dns_settings.SLAVE_SERVER_LIST:
            for slave_ip in dns_settings.SLAVE_SERVER_LIST:
                print("=== checkpoint ===")
                api_url = "http://%s:%s/dns/api/cluster/notice" % (slave_ip, dns_settings.API_PORT)
                post_data['notice_from_master'] = notice
                ret_data[slave_ip] = api_caller.post_caller(api_url, post_data)
        return ret_data

    def dataCheckForClusterName(self, cluster_name):
        if cluster_name not in dns_settings.CLUSTER_NAME_DEFINE:
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'cluster_name'", status=400)
        else:
            return cluster_name
    def genUUID(self, length=64):
        seed = '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return ''.join([ seed[random.randint(0,len(seed) - 1)] for i in range(length)])
