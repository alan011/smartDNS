from django.http                  import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators      import method_decorator
from django.views.generic         import View

from .ns_api_auth     import NSApiAuth
from .ns_api_common   import NSApiCommon
from dns              import dns_settings
from dns.models       import BindConfigView
from dns.ns_factory.ns_config_handler import BindNamedConfHandler

import json, re


class NSApiViewCommon(NSApiAuth, NSApiCommon):
    def dataCheckForViewName(self,view_name):
        ### check 'view_name'
        if not isinstance(view_name,str):
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'view_name'", status=400)
        elif re.search("[^a-zA-Z0-9\.\_\-]", view_name):
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'view_name'", status=400)
        return view_name

    def dataCheckForAclName(self,acl_name):
        ### check 'acl_name'
        if acl_name not in [ a for a,b in dns_settings.ACL_NAME_DEFINE ]:
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'acl_name'", status=400)
        else:
            return acl_name

    def dataCheckForAllowedKey(self,allowed_key):
        ### check 'allowed_key'
        if allowed_key not in dns_settings.VIEW_KEY_DEFINE:
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'allowed_key'", status=400)
        else:
            return allowed_key


@method_decorator(csrf_exempt, name='dispatch')
class NSApiViewAdd(View, NSApiViewCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'view_name',        ### Type str: view name string, reg match '^[a-zA-Z0-9\.\_\-]*$' is required.
                    'readable_name',    ### Type str: Maybe Chinese words.
                    'acl_name',         ### Type str: Choice from 'dns_settings.ACL_NAME_DEFINE'
                    'allowed_key',      ### Type str: Choice from 'dns_settings.VIEW_KEY_DEFINE'
                    'description',      ### Type str: Any string inlcude a ''
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {"name"       : self.dataCheckForViewName(post_data['view_name']),
                    "readable_name": str(post_data['readable_name']),
                    "acl_name"   : self.dataCheckForAclName(post_data['acl_name']),
                    "allowed_key": self.dataCheckForAllowedKey(post_data['allowed_key']),
                    "description": str(post_data['description']),  ### 'description' field do not need to check.
                    }
        if dns_settings.ENABLE_MULTI_CLUSTERS:
            if post_data.get('cluster_name'):
                ret_data['cluster_name'] = self.dataCheckForClusterName(post_data.get('cluster_name'))
            else:
                ret_data['cluster_name'] = ''    ### For Re-Add a view.
        return super().dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = self.prepare_post(request)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### write post data to db.
        view_queryset = self.checkObjExist({'name':data_check_result['name']}, BindConfigView)
        if view_queryset:
            view_obj = view_queryset.get(name=data_check_result['name'])
            if view_obj.is_deleted == 0:
                self.response_data['message'] += "To add BIND view: view '%s' aready existed, DB operation ignored. " % data_check_result['name']
            else:
                self.readdAnObject(view_obj, data_check_result)
                self.response_data['message'] += "To add BIND view: add view '%s' to DB successfully. " % data_check_result['name']
        else:
            new_view_obj = BindConfigView(**data_check_result)
            new_view_obj.save()
            self.response_data['message'] += "To add BIND view: add view '%s' to DB successfully. " % data_check_result['name']

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')


@method_decorator(csrf_exempt, name='dispatch')
class NSApiViewDelete(View, NSApiViewCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'view_name',        ### Type str: view name string, reg match '^[a-zA-Z0-9\.\_\-]*$' is required.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {"name":self.dataCheckForViewName(post_data['view_name']),
                    }
        return super().dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = super().prepare_post(request)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### Write post data to db.
        view_queryset = self.checkObjExist({'name':data_check_result['name']}, BindConfigView)
        if not view_queryset:
            self.response_data['message'] += "To delete bind view: view '%s' not exist, nothing to do. " % data_check_result['name']
        else:
            view_obj = view_queryset.get(**data_check_result)
            if view_obj.is_deleted:
                if view_obj.is_applied:
                    self.response_data['message'] += "To delete BIND view: view '%s' has already been deleted yet, nothing to do. " % data_check_result['name']
                else:
                    self.response_data['message'] += "To delete BIND view: view '%s' has already been deleted in DB, but not applied to service. " % data_check_result['name']
            else:
                view_obj.is_deleted = 1
                view_obj.is_applied = 0
                view_obj.save()
                self.response_data['message'] += "To delete BING view: delete view '%s' successfully, please remember to apply it to service. " % data_check_result['name']

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')


@method_decorator(csrf_exempt, name='dispatch')
class NSApiViewModify(View, NSApiViewCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'view_name',        ### Type str: view name string, reg match '^[a-zA-Z0-9\.\_\-]*$' is required.
                    'readable_name',    ### Type str: Maybe Chinese words.
                    'acl_name',         ### Type str: Choice from 'dns_settings.ACL_NAME_DEFINE'
                    'allowed_key',      ### Type str: Choice from 'dns_settings.VIEW_KEY_DEFINE'
                    'description',      ### Type str: Any string inlcude a ''.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {}
        if "view_name" in post_data:
            ret_data['name'] = self.dataCheckForViewName(post_data['view_name'])
        else:
            return HttpResponse("ERROR: key field 'view_name' must be provided.", status=400)

        if "readable_name" in post_data:
            ret_data["readable_name"] = str(post_data['readable_name'])
        if "acl_name" in post_data:
            ret_data["acl_name"]    = self.dataCheckForAclName(post_data['acl_name'])
        if "allowed_key" in post_data:
            ret_data["allowed_key"] = self.dataCheckForAllowedKey(post_data['allowed_key'])
        if "description" in post_data:
            ret_data["description"] = str(post_data["description"])
        if dns_settings.ENABLE_MULTI_CLUSTERS and post_data.get('cluster_name') is not None:
            ret_data['cluster_name'] = self.dataCheckForClusterName(post_data.get('cluster_name'))

        return super().dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = self.prepare_post(request, field_require=False)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### Write post data to db.
        view_queryset = self.checkObjExist({'name':data_check_result['name']}, BindConfigView)
        if not view_queryset:
            self.response_data['message'] += "To modify BIND view: view '%s' not exist, nothing to do. " % data_check_result['name']
            self.response_data['result'] = 'FAILED'
        else:
            view_obj = view_queryset.get(name=data_check_result['name'])
            if view_obj.is_deleted == 1:
                self.response_data['message'] += "To modify BIND view: view '%s' has been deleted yet, nothing to do. " % data_check_result['name']
                self.response_data['result'] = 'FAILED'
            else:
                if "description" in data_check_result:
                    view_obj.description = data_check_result['description']
                if "acl_name" in data_check_result and view_obj.acl_name != data_check_result['acl_name']:
                    view_obj.acl_name = data_check_result['acl_name']
                    view_obj.is_applied = 0
                if 'allowed_key' in data_check_result and view_obj.allowed_key != data_check_result['allowed_key']:
                    view_obj.allowed_key = data_check_result['allowed_key']
                    view_obj.is_applied = 0
                if 'cluster_name' in data_check_result and view_obj.cluster_name !=  data_check_result['cluster_name']:
                    view_obj.cluster_name = data_check_result['cluster_name']
                    view_obj.is_applied = 0
                if 'readable_name' in data_check_result and view_obj.readable_name !=  data_check_result['readable_name']:
                    view_obj.readable_name = data_check_result['readable_name']

                view_obj.save()

                if view_obj.is_applied == 0:
                    self.response_data['message'] += "To modify BIND view: modify view '%s' successfully, please remember to apply it to service. " % data_check_result['name']
                else:
                    self.response_data['message'] += "To modify BIND view: modify view '%s' successfully, no service affected attribute changed, no need to apply to service. " % data_check_result['name']

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')

@method_decorator(csrf_exempt, name='dispatch')
class NSApiViewQuery(View, NSApiViewCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'get_all',          ### Type str: 'get_all' is the only value.
                    'is_applied',       ### Type str: a choice in ('applied','unapplied')
                    'view_name',        ### Type str: view name string, reg match '^[a-zA-Z0-9\.\_\-]*$' is required.
                    'acl_name',         ### Type str: Choice from 'dns_settings.ACL_NAME_DEFINE'
                    'allowed_key',      ### Type str: Choice from 'dns_settings.VIEW_KEY_DEFINE'
                    'description',      ### Type str: Any string inlcude a ''.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {}
        if 'get_all'     in post_data:
            if post_data['get_all'] == 'get_all':
                ret_data['get_all'] = 'get_all'
                return ret_data
            else:
                return HttpResponse("ERROR: post data illegal. Illegal value for field 'get_all'", status=400)

        if "view_name"   in post_data:
            ret_data["name"]   = self.dataCheckForViewName(post_data['view_name'])
        if "acl_name"    in post_data:
            ret_data["acl_name"]    = self.dataCheckForAclName(post_data['acl_name'])
        if "allowed_key" in post_data:
            ret_data["allowed_key"] = self.dataCheckForAllowedKey(post_data['allowed_key'])
        if post_data.get('cluster_name'):
            ret_data['cluster_name'] = self.dataCheckForClusterName(post_data.get('cluster_name'))
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
        data_check_result = self.prepare_post(request, field_require=False)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### Query data from db.
        if 'get_all' in data_check_result:
            queryset = BindConfigView.objects.filter(is_deleted=0)
        else:
            filter_dict = {'is_deleted': 0}
            if 'is_applied' in data_check_result:
                filter_dict['is_applied'] = data_check_result.pop('is_applied')
            for field in data_check_result:
                filter_dict[field + '__icontains'] = data_check_result[field]

            queryset = BindConfigView.objects.filter(**filter_dict)

        ### Make query data for return.
        self.response_data['query_data'] = []
        if not queryset.exists():
            self.response_data['message'] += 'No BIND view found. '
        else:
            for obj in queryset.order_by('id'):
                a_view = {'view_name'  : obj.name,
                         'readable_name': obj.readable_name,
                         'acl_name'   : obj.acl_name,
                         'allowed_key': obj.allowed_key,
                         'description': obj.description,
                         'add_time'   : obj.add_time.strftime('%Y-%m-%d %H:%M:%S'),
                         'is_applied' : obj.is_applied,
                         }
                if dns_settings.ENABLE_MULTI_CLUSTERS:
                    a_view['cluster_name'] = obj.cluster_name
                    a_view['cluster_name_alias'] = dns_settings.CLUSTER_NAME_DEFINE.get(obj.cluster_name)
                self.response_data['query_data'].append(a_view)
            self.response_data['message'] += '%d BIND views found.' % len(self.response_data['query_data'])

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')


@method_decorator(csrf_exempt, name='dispatch')
class NSApiViewApply(View, NSApiViewCommon):
    """
    To write the BIND main configure file '/etc/named.conf' according to views in DB.
    Note: this API only write file, never restart the 'named' service.
    """
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'view_apply',       ### Type str: 'view_apply' is the only value.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {}
        if "view_apply" in post_data and post_data['view_apply'] == 'view_apply':
            ret_data['view_apply'] = 'view_apply'
        else:
            return HttpResponse('ERROR: post data illegal.', status=400)
        return ret_data

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = super().prepare_post(request)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### write named.conf configure file.
        named_config_handler = BindNamedConfHandler()
        file_write_ret = named_config_handler.configBindNamedConf()
        if not isinstance(file_write_ret, dict):
            return HttpResponse(str(file_write_ret), status=400)

        ### notice slaves to apply
        if dns_settings.SLAVE_SERVER_LIST and dns_settings.THIS_IS_MASTER:
            slave_apply_result = self.notice_slaves('APPLY_NAMED_CONF')
            print(slave_apply_result)

        return HttpResponse(json.dumps(file_write_ret), content_type='application/json')
