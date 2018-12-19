from django.http                  import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators      import method_decorator
from django.views.generic         import View

from .ns_api_auth     import NSApiAuth
from .ns_api_common   import NSApiCommon
from dns              import dns_settings
from dns.models       import BindConfigACL
from dns.tools        import validateSubnet, validateIP
from dns.ns_factory.ns_config_handler import BindACLConfigHandler

import json


class NSApiACLCommon(NSApiAuth, NSApiCommon):
    def dataCheckForAclSubnet(self,acl_subnet):
        ### check 'acl_subnet'
        if not isinstance(acl_subnet,str):
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'acl_subnet'", status=400)
        else:
            if validateIP(acl_subnet) or validateSubnet(acl_subnet):
                return acl_subnet
            else:
                return HttpResponse("ERROR: post data illegal. Illegal value for field 'acl_subnet'", status=400)

    def dataCheckForAclName(self, acl_name):
        ### check 'acl_name'
        if acl_name not in [ a for a,b in dns_settings.ACL_NAME_DEFINE ]:
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'acl_name'", status=400)
        else:
            return acl_name


@method_decorator(csrf_exempt, name='dispatch')
class NSApiACLAdd(View, NSApiACLCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'acl_subnet',       ### Type str: A IP address, or subnet like '172.16.40.0/24'.
                    'acl_name',         ### Type str: Choice from 'dns_settings.ACL_NAME_DEFINE'
                    # 'resolv_area',     ### Type str: Choice from 'RESOLV_AREA_CHOICES'
                    'description',      ### Type str: Any string inlcude a ''.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {"subnet":       self.dataCheckForAclSubnet(post_data['acl_subnet']),
                    "acl_name":     self.dataCheckForAclName(post_data['acl_name']),
                    # "resolv_area":self.dataCheckForResolvArea(post_data['resolv_area']),
                    "description":  str(post_data['description']),  ### 'description' field do not need to check.
                    }
        if dns_settings.ENABLE_MULTI_CLUSTERS:
            if post_data.get('cluster_name'):
                ret_data['cluster_name'] = self.dataCheckForClusterName(post_data.get('cluster_name'))
            else:
                ret_data['cluster_name'] = ''    ### For Re-Add a iplist.

        return super().dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = super().prepare_post(request)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### write post data to db.
        acl_queryset = self.checkObjExist({'subnet':data_check_result['subnet']}, BindConfigACL)
        if acl_queryset:
            subnet_obj = acl_queryset.get(subnet=data_check_result['subnet'])
            if subnet_obj.is_deleted == 0:
                self.response_data['message'] += "To add ACL record: subnet '%s' aready existed, DB operation ignored. " % data_check_result['subnet']
            else:
                self.readdAnObject(subnet_obj, data_check_result)
                self.response_data['message'] += "To add ACL record: add subnet '%s' to DB successfully. " % data_check_result['subnet']
        else:
            new_acl_obj = BindConfigACL(**data_check_result)
            new_acl_obj.save()
            self.response_data['message'] += "To add ACL record: add subnet '%s' to DB successfully. " % data_check_result['subnet']

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')


@method_decorator(csrf_exempt, name='dispatch')
class NSApiACLDelete(View, NSApiACLCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'acl_subnet',       ### Type str: A IP address, or subnet like '172.16.40.0/24'.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {"subnet":self.dataCheckForAclSubnet(post_data['acl_subnet']),
                    }
        return super().dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = super().prepare_post(request)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### Write post data to db.
        acl_queryset = self.checkObjExist({'subnet':data_check_result['subnet']}, BindConfigACL)
        if not acl_queryset:
            self.response_data['message'] += "To delete ACL record: subnet '%s' not exist, nothing to do. " % data_check_result['subnet']
        else:
            acl_obj = acl_queryset.get(**data_check_result)
            if acl_obj.is_deleted:
                if acl_obj.is_applied:
                    self.response_data['message'] += "To delete ACL record: subnet '%s' has already been deleted, nothing to do. " % data_check_result['subnet']
                else:
                    self.response_data['message'] += "To delete ACL record: subnet '%s' has already been deleted in DB, but not applied to service. " % data_check_result['subnet']
            else:
                acl_obj.is_deleted = 1
                acl_obj.is_applied = 0
                acl_obj.save()
                self.response_data['message'] += "To delete ACL record: delete subnet '%s' successfully, please remember to apply it to service. " % data_check_result['subnet']

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')


@method_decorator(csrf_exempt, name='dispatch')
class NSApiACLModify(View, NSApiACLCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'acl_subnet',       ### Type str: A IP address, or subnet like '172.16.40.0/24', as the key field.
                    'acl_name',         ### Type str: Choice from 'dns_settings.ACL_NAME_DEFINE'
                    # 'resolv_area',      ### Type str: Choice from 'RESOLV_AREA_CHOICES'
                    'description',      ### Type str: Any string inlcude a ''.
                    'cluster_name',     ### Type str: Choice from 'dns_settings.CLUSTER_NAME_DEFINE'
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {}
        if "acl_subnet" in post_data:
            ret_data['subnet'] = self.dataCheckForAclSubnet(post_data['acl_subnet'])
        else:
            return HttpResponse("ERROR: key field 'acl_subnet' must be provided.", status=400)

        if "acl_name" in post_data:
            ret_data["acl_name"]    = self.dataCheckForAclName(post_data['acl_name'])
        if "description" in post_data:
            ret_data["description"] = str(post_data["description"])
        if dns_settings.ENABLE_MULTI_CLUSTERS and post_data.get('cluster_name') is not None:
            ret_data["cluster_name"] = self.dataCheckForClusterName(post_data["cluster_name"])

        return super().dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = super().prepare_post(request, field_require=False)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### Write post data to db.
        acl_queryset = self.checkObjExist({'subnet':data_check_result['subnet']}, BindConfigACL)
        if not acl_queryset:
            self.response_data['message'] += "To modify ACL record: subnet '%s' not exist, nothing to do. " % data_check_result['subnet']
            self.response_data['result'] = 'FAILED'
        else:
            acl_obj = acl_queryset.get(subnet=data_check_result['subnet'])
            if acl_obj.is_deleted == 1:
                self.response_data['message'] += "To modify ACL record: subnet '%s' has been deleted yet, nothing to do. " % data_check_result['subnet']
                self.response_data['result'] = 'FAILED'
            else:
                if "description" in data_check_result:
                    acl_obj.description = data_check_result['description']
                if "acl_name" in data_check_result and acl_obj.acl_name != data_check_result['acl_name']:
                    acl_obj.acl_name = data_check_result['acl_name']
                    acl_obj.is_applied = 0
                if "cluster_name" in data_check_result and acl_obj.cluster_name != data_check_result['cluster_name']:
                    acl_obj.cluster_name = data_check_result['cluster_name']
                    acl_obj.is_applied = 0

                acl_obj.save()

                if acl_obj.is_applied == 0:
                    self.response_data['message'] += "To modify ACL record: modify subnet '%s' successfully, please remember to apply it to service. " % data_check_result['subnet']
                else:
                    self.response_data['message'] += "To modify ACL record: modify subnet '%s' successfully, no service affected attribute changed, no need to apply to service. " % data_check_result['subnet']

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')

@method_decorator(csrf_exempt, name='dispatch')
class NSApiACLQuery(View, NSApiACLCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'get_all',          ### Type str: 'get_all' is the only value.
                    'is_applied',       ### Type str: a choice in ('applied','unapplied')
                    'acl_subnet',
                    'acl_name',
                    'description',
                    'cluster_name',     ### Type str: Choice from 'dns_settings.CLUSTER_NAME_DEFINE'
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {}
        if 'get_all'     in post_data:
            if post_data['get_all'] == 'get_all':
                ret_data['get_all'] = 'get_all'
                return ret_data
            else:
                return HttpResponse("ERROR: post data illegal. Illegal value for field 'get_all'", status=400)
        if "acl_subnet"  in post_data:
            ret_data["subnet"]      = self.dataCheckForAclSubnet(post_data['acl_subnet'])
        if "acl_name"    in post_data:
            ret_data["acl_name"]    = self.dataCheckForAclName(post_data['acl_name'])
        if "cluster_name" in post_data:
            ret_data["cluster_name"] = self.dataCheckForClusterName(post_data['cluster_name'])
        if "description" in post_data:
            ret_data["description"] = str(post_data["description"])
        if 'is_applied'  in post_data:
            if post_data['is_applied']   == 'applied':
                ret_data['is_applied'] = 1
            elif post_data['is_applied'] == 'unapplied':
                ret_data['is_applied'] = 0
            else:
                return HttpResponse("ERROR: post data illegal. Illegal value for field 'is_applied'", status=400)

        if not ret_data:
            return HttpResponse("ERROR: post data illegal. No query field provided.", status=400)

        return super().dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = super().prepare_post(request, field_require=False)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### Query data from db.
        if 'get_all' in data_check_result:
            queryset = BindConfigACL.objects.filter(is_deleted=0)
        else:
            filter_dict = {'is_deleted': 0}
            if 'is_applied' in data_check_result:
                filter_dict['is_applied'] = data_check_result.pop('is_applied')
            for field in data_check_result:
                filter_dict[field + '__icontains'] = data_check_result[field]

            queryset = BindConfigACL.objects.filter(**filter_dict)

        ### Make query data for return.
        self.response_data['query_data'] = []
        if not queryset.exists():
            self.response_data['message'] += 'No ACL record found. '
        else:
            for obj in queryset.order_by('id'):
                acl_record = {'acl_subnet' : obj.subnet,
                              'acl_name'   : obj.acl_name,
                              'description': obj.description,
                              'add_time'   : obj.add_time.strftime('%Y-%m-%d %H:%M:%S'),
                              'is_applied' : obj.is_applied,
                              }
                if dns_settings.ENABLE_MULTI_CLUSTERS:
                    acl_record['cluster_name'] = obj.cluster_name
                    acl_record['cluster_name_alias'] = dns_settings.CLUSTER_NAME_DEFINE.get(obj.cluster_name)
                self.response_data['query_data'].append(acl_record)
            self.response_data['message'] += '%d ACL records found.' % len(self.response_data['query_data'])

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')


@method_decorator(csrf_exempt, name='dispatch')
class NSApiACLApply(View, NSApiACLCommon):
    """
    An NS API to apply ACL records in DB to BIND configure file.
    Note: this API only write file, never restart the 'named' service.
    """
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'acl_apply',        ### Type str: 'acl_apply' is the only value.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {}
        if "acl_apply" in post_data and post_data['acl_apply'] == 'acl_apply':
            ret_data['acl_apply'] = 'acl_apply'
        else:
            return HttpResponse('ERROR: post data illegal.', status=400)
        return ret_data

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = super().prepare_post(request)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### write Acl configure file.
        acl_config_handler = BindACLConfigHandler()
        apply_ret = acl_config_handler.configBindACL()
        if not isinstance(apply_ret, dict):
            return HttpResponse(str(apply_ret), status=400)

        ### notice slaves to apply
        if dns_settings.SLAVE_SERVER_LIST and dns_settings.THIS_IS_MASTER:
            slave_apply_result = self.notice_slaves('APPLY_ACL')
            print(slave_apply_result)

        return HttpResponse(json.dumps(apply_ret), content_type='application/json')
