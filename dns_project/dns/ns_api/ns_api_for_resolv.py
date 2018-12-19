from django.http                  import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators      import method_decorator
from django.views.generic         import View
from django.db.models             import Q

from .ns_api_auth     import NSApiAuth
from .ns_api_common   import NSApiCommon
from dns              import dns_settings
from dns.models       import BindNSRecord, BindConfigZone, BindConfigView
from dns.tools        import validateSubnet, validateIP
from dns.ns_factory.ns_config_handler import BindResolvHandler

import json, re


class NSApiResolvCommon(NSApiAuth, NSApiCommon):
    def dataCheckForResolvName(self,resolv_name):
        if not isinstance(resolv_name,str):
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'resolv_subnet'. ", status=400)
        else:
            if re.search('(^[a-zA-Z0-9][a-zA-Z0-9\.\-]*[a-zA-Z0-9]$)|(^[a-zA-Z0-9]$)|(^@$)',resolv_name):
                return resolv_name
            else:
                Response("ERROR: post data illegal. Illegal value for field 'resolv_name'. ", status=400)

    def dataCheckForRecordType(self, record_type):
        if record_type not in [ a for a,b in dns_settings.RECORD_TYPE_CHOICES ]:
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'record_type'. ", status=400)
        else:
            return record_type

    def dataCheckForResolvAddr(self, resolv_addr, record_type='A'):
        if not isinstance(resolv_addr,str):
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'resolv_addr'. ", status=400)
        if record_type in ('A', 'MX','AAAA') and not validateIP(resolv_addr):
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'resolv_addr', with record type '{}'. ".format(record_type) , status=400)
        if record_type == 'CNAME' and not re.search('(^[a-zA-Z][a-zA-Z0-9\.\-]*[a-zA-Z0-9]$)|(^[a-zA-Z]$)',resolv_addr):
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'resolv_addr', with record type 'CNAME'. ", status=400)
        return resolv_addr

    def dataCheckForZoneBelong(self, zone_belong, filter_by_id=False):
        if filter_by_id:
            if not isinstance(zone_belong, int):
                return HttpResponse("ERROR: post data illegal. Illegal value for field 'zone_id'. ", status=400)
            zone_queryset = BindConfigZone.objects.filter(id=zone_belong)
            if not zone_queryset.exists():
                return HttpResponse("ERROR: No zone object found with field 'zone_id: %d'. " % zone_belong, status=400)
            return zone_queryset.get(id=zone_belong)
        else:
            if not isinstance(zone_belong,str):
                return HttpResponse("ERROR: post data illegal. Illegal value for field 'zone_name'. ", status=400)
            zone_queryset = BindConfigZone.objects.filter(name=zone_belong)
            if not zone_queryset.exists():
                return HttpResponse("ERROR: No zone object found with field 'zone_name: %s'. " % zone_belong, status=400)
            return zone_queryset.get(name=zone_belong)

    def dataCheckForViewBelong(self, view_belong):
        if not isinstance(view_belong,str):
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'view_belong'. ", status=400)
        if view_belong.upper() == 'DEFAULT':
            return None

        view_queryset = BindConfigView.objects.filter(name=view_belong)
        if not view_queryset.exists():
            return HttpResponse("ERROR: No view object found with field 'view_belong: %s'. " % view_belong, status=400)
        return view_queryset.get(name=view_belong)

    def dataCheckForTTLSeconds(self, ttl_seconds):
        if not ttl_seconds in [ a for a,b in dns_settings.TTL_CHOICES ]:
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'ttl_seconds'. ", status=400)
        return ttl_seconds

    def dataCheckForIsDisabled(self, is_disabled):
        if not is_disabled in (0, 1):
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'is_disabled'. ", status=400)
        return is_disabled

    def dataCheckForResolvID(self, resolv_id):
        if not isinstance(resolv_id, int):
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'resolv_id'. ", status=400)
        return resolv_id
    def dataCheckForResolvUUID(self, resolv_uuid):
        if len(str(resolv_uuid)) != 64:
            return HttpResponse("ERROR: post data illegal. 'resolv_uuid' must be a 64-byte-length random string. ", status=400)
        return str(resolv_uuid)

@method_decorator(csrf_exempt, name='dispatch')
class NSApiResolvAdd(View, NSApiResolvCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'resolv_name',      ### Type str: require RE match: '(^[a-zA-Z][a-zA-Z0-9\.\-]*[a-zA-Z0-9]$)|(^[a-zA-Z]$)'
                    'record_type',      ### Type str: Choice from 'dns_settings.RECORD_TYPE_CHOICES'
                    'resolv_addr',      ### Type str: requires special string according to 'record_type'.
                    'zone_belong',      ### Type str: zone name required RE match: '^[a-zA-Z0-9\.\-]+$'
                    'view_belong',      ### Type str: view name required RE match: '^[a-zA-Z0-9\.\-\_]+$'
                    'ttl_seconds',      ### Type int: Choice from 'dns_settings.TTL_CHOICES'
                    'description',      ### Type str: Any string inlcude a ''.
                    'resolv_uuid',      ### Type str: a 64-byte-length random string.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {"name":        self.dataCheckForResolvName(post_data['resolv_name']),
                    "record_type": self.dataCheckForRecordType(post_data['record_type']),
                    "resolv_addr": self.dataCheckForResolvAddr(post_data['resolv_addr'],post_data['record_type']),
                    "zone_belong": self.dataCheckForZoneBelong(post_data['zone_belong']),
                    "view_belong": self.dataCheckForViewBelong(post_data['view_belong']),
                    "ttl_seconds": self.dataCheckForTTLSeconds(post_data['ttl_seconds']),
                    "description": str(post_data['description']),  ### 'description' field do not need to check.
                    "uuid":        self.dataCheckForResolvUUID(post_data['resolv_uuid']),
                    }
        if not ret_data['view_belong']:
            ret_data.pop('view_belong')
        if dns_settings.ENABLE_MULTI_CLUSTERS:
            if post_data.get('cluster_name'):
                ret_data['cluster_name'] = self.dataCheckForClusterName(post_data.get('cluster_name'))
            else:
                ret_data['cluster_name'] = ''    ### For Re-Add a resolv.
        ret_data['is_disabled'] = 0
        return super().dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = self.prepare_post(request)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### Check resolv existence by the given uuid.
        queryset = self.checkObjExist({'uuid':data_check_result['uuid']}, BindNSRecord)
        if queryset:
            self.response_data['message'] += "ERROR: To add resolv record failed: resolv_uuid '%s' has already existed. " % data_check_result['uuid']
        else:
            ### write post data to db.
            new_resolv_obj = BindNSRecord(**data_check_result)
            new_resolv_obj.save()
            self.response_data['message'] += "To add resolv record: add resolv record '%s' in zone '%s' to DB successfully. " % (data_check_result['name'], data_check_result['zone_belong'].name)

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')


@method_decorator(csrf_exempt, name='dispatch')
class NSApiResolvDelete(View, NSApiResolvCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'resolv_uuid',      ### Type str: a 64-byte-length random string.
                   ]
    def dataCheckInDetail(self, post_data):
        return {'uuid': self.dataCheckForResolvUUID(post_data['resolv_uuid'])}

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = self.prepare_post(request)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### Write post data to db.
        resolv_queryset = self.checkObjExist(data_check_result, BindNSRecord)
        if not resolv_queryset:
            self.response_data['message'] += "To delete resolv: resolv_uuid '%s' not exist, nothing to do. " % data_check_result['uuid']
        else:
            resolv_obj = resolv_queryset.get(**data_check_result)
            if resolv_obj.is_deleted:
                if resolv_obj.is_applied:
                    self.response_data['message'] += "To delete resolv: resolv_uuid '%s' has already been deleted, nothing to do. " % data_check_result['uuid']
                else:
                    self.response_data['message'] += "To delete resolv: resolv_uuid '%s' has already been deleted in DB, but not applied to service. " % data_check_result['uuid']
            else:
                resolv_obj.is_deleted = 1
                resolv_obj.is_applied = 0
                resolv_obj.save()
                self.response_data['message'] += "To delete resolv: delete resolv_uuid '%s' successfully, please remember to apply it to service. " % data_check_result['uuid']

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')


@method_decorator(csrf_exempt, name='dispatch')
class NSApiResolvModify(View, NSApiResolvCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'resolv_uuid',      ### Type str: a 64-byte-length random string.
                    'record_type',      ### Type str: Choice from 'dns_settings.RECORD_TYPE_CHOICES'
                    'resolv_addr',      ### Type str: requires special string according to 'record_type'.
                    'view_belong',      ### Type str: view name required RE match: '^[a-zA-Z0-9\.\-\_]+$'
                    'ttl_seconds',      ### Type int: Choice from 'dns_settings.TTL_CHOICES'
                    'description',      ### Type str: Any string inlcude a ''.
                    'is_disabled',      ### Type int: Choices from: 0 or 1.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {}
        if "resolv_uuid" in post_data:
            ret_data['uuid'] = self.dataCheckForResolvUUID(post_data['resolv_uuid'])
        else:
            return HttpResponse("ERROR: key field 'resolv_uuid' must be provided.", status=400)

        if "record_type" in post_data:
            ret_data["record_type"] = self.dataCheckForRecordType(post_data['record_type'])
        if "resolv_addr" in post_data:
            ret_data["resolv_addr"] = self.dataCheckForResolvAddr(post_data['resolv_addr'],post_data['record_type'])
        if "view_belong" in post_data:
            ret_data["view_belong"] = self.dataCheckForViewBelong(post_data['view_belong'])
        if "ttl_seconds" in post_data:
            ret_data["ttl_seconds"] = self.dataCheckForTTLSeconds(post_data['ttl_seconds'])
        if "is_disabled" in post_data:
            ret_data["is_disabled"] = self.dataCheckForIsDisabled(post_data['is_disabled'])
        if "description" in post_data:
            ret_data["description"] = str(post_data["description"])
        if dns_settings.ENABLE_MULTI_CLUSTERS and post_data.get('cluster_name') is not None:
            ret_data['cluster_name'] = self.dataCheckForClusterName(post_data.get('cluster_name'))

        return super().dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = super().prepare_post(request, field_require=False)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### Write post data to db.
        resolv_queryset = self.checkObjExist({'uuid':data_check_result['uuid']}, BindNSRecord)
        if not resolv_queryset:
            self.response_data['message'] += "To modify resolv record: resolv uuid '%s' not exist, nothing to do. " % data_check_result['uuid']
            self.response_data['result'] = 'FAILED'
        else:
            resolv_obj = resolv_queryset.get(uuid=data_check_result['uuid'])
            if resolv_obj.is_deleted == 1:
                self.response_data['message'] += "ERROR: To modify resolv: resolv_uuid '%s' has been deleted. " % data_check_result['uuid']
                self.response_data['result'] = 'FAILED'
            else:
                ### Modify attributes do not need to apply first.
                if "description" in data_check_result:
                    resolv_obj.description = data_check_result['description']

                ### Modify attibutes that do need to apply.
                if "record_type" in data_check_result and resolv_obj.record_type != data_check_result['record_type']:
                    resolv_obj.record_type = data_check_result['record_type']
                    resolv_obj.is_applied = 0
                if "resolv_addr" in data_check_result and resolv_obj.resolv_addr != data_check_result['resolv_addr']:
                    resolv_obj.resolv_addr = data_check_result['resolv_addr']
                    resolv_obj.is_applied = 0
                if "view_belong" in data_check_result and resolv_obj.view_belong != data_check_result['view_belong']:
                    resolv_obj.view_belong = data_check_result['view_belong']
                    resolv_obj.is_applied = 0
                if "ttl_seconds" in data_check_result and resolv_obj.ttl_seconds != data_check_result['ttl_seconds']:
                    resolv_obj.ttl_seconds = data_check_result['ttl_seconds']
                    resolv_obj.is_applied = 0
                if "is_disabled" in data_check_result and resolv_obj.is_disabled != data_check_result['is_disabled']:
                    resolv_obj.is_disabled = data_check_result['is_disabled']
                    resolv_obj.is_applied = 0
                if "cluster_name" in data_check_result and resolv_obj.cluster_name != data_check_result['cluster_name']:
                    resolv_obj.cluster_name = data_check_result.get("cluster_name")
                    resolv_obj.is_applied = 0

                resolv_obj.save()

                if resolv_obj.is_applied == 0:
                    self.response_data['message'] += "To modify resolv: modify resolv_uuid '%s' successfully, please remember to apply it to service. " % data_check_result['uuid']
                else:
                    self.response_data['message'] += "To modify resolv: modify resolv_uuid '%s' successfully, no service affected attribute changed, no need to apply to service. " % data_check_result['uuid']

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')

@method_decorator(csrf_exempt, name='dispatch')
class NSApiResolvQuery(View, NSApiResolvCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'resolv_uuid',      ### Type str: a 64-byte-length random string.
                    'zone_id',          ### Type int: ID of zone object.
                    'zone_name'         ### Type str: zone name required RE match: '^[a-zA-Z0-9\.\-]+$'
                    'get_all',          ### Type str: 'get_all' is the only value.
                    'resolv_name',      ### Type str: require RE match: '(^[a-zA-Z][a-zA-Z0-9\.\-]*[a-zA-Z0-9]$)|(^[a-zA-Z]$)'
                    'view_belong',      ### Type str: view name required RE match: '^[a-zA-Z0-9\.\-\_]+$'
                    'record_type',      ### Type str: Choice from 'dns_settings.RECORD_TYPE_CHOICES'
                    'resolv_addr',      ### Type str: requires special string according to 'record_type'.
                    'ttl_seconds',      ### Type int: Choice from 'dns_settings.TTL_CHOICES'
                    'description',      ### Type str: Any string inlcude a ''.
                    'is_disabled',      ### Type int: Choices from: 'disabled' or 'enabled'.
                    'is_applied',       ### Type int: Choices from: 'applied' or 'unapplied'.
                    'search_value',     ### Type str: for implicitly search in multi-fields.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {}
        if 'all_zones' in post_data:
            if post_data['all_zones'] == 'all_zones':
                ret_data['all_zones'] = 'all_zones'
                return ret_data
            else:
                return HttpResponse("ERROR: post data illegal. Illegal value for field 'all_zones'", status=400)

        if 'resolv_uuid' in post_data:
            ret_data["uuid"] = str(post_data["resolv_uuid"])
            return ret_data

        if 'zone_id' in post_data:
            if not isinstance(post_data['zone_id'], int):
                if not re.search('^[0-9]+$', str(post_data['zone_id'])):
                    return HttpResponse("ERROR: Illegal value for key field 'zone_id': %s" % str(post_data['zone_id']))
                post_data['zone_id'] = int(post_data['zone_id'])
            ret_data['zone_belong'] = self.dataCheckForZoneBelong(post_data['zone_id'], filter_by_id=True)
        elif 'zone_name' in post_data:
            ret_data['zone_belong'] = self.dataCheckForZoneBelong(post_data['zone_name'], filter_by_id=False)
        else:
            return HttpResponse("ERROR: post data illegal. Key field 'zone_id' or 'zone_name' must be provided.")

        if 'get_all' in post_data:
            if post_data['get_all'] == 'get_all':
                ret_data['get_all'] = 'get_all'
                return ret_data
            else:
                return HttpResponse("ERROR: post data illegal. Illegal value for field 'get_all'", status=400)
        ### fields search as filter
        if "resolv_name" in post_data:
            ret_data['name'] = self.dataCheckForResolvName(post_data['resolv_name'])
        if "view_belong" in post_data:
            ret_data['view_belong'] = self.dataCheckForViewBelong(post_data['view_belong'])
        if "record_type" in post_data:
            ret_data["record_type"] = self.dataCheckForRecordType(post_data["record_type"])
        if "resolv_addr" in post_data:
            ret_data["resolv_addr"] = post_data["resolv_addr"]
        if 'ttl_seconds'  in post_data:
            ret_data['ttl_seconds'] = self.dataCheckForTTLSeconds(post_data['ttl_seconds'])
        if 'is_applied'  in post_data:
            if post_data['is_applied']   == 'applied':
                ret_data['is_applied'] = 1
            elif post_data['is_applied'] == 'unapplied':
                ret_data['is_applied'] = 0
            else:
                return HttpResponse("ERROR: post data illegal. Illegal value for field 'is_applied'", status=400)
        if 'is_disabled'  in post_data:
            if post_data['is_disabled']   == 'disabled':
                ret_data['is_disabled'] = 1
            elif post_data['is_disabled'] == 'enabled':
                ret_data['is_disabled'] = 0
            else:
                return HttpResponse("ERROR: post data illegal. Illegal value for field 'is_disabled'", status=400)
        if 'cluster_name' in post_data:
            ret_data['cluster_name'] = self.dataCheckForClusterName(post_data['cluster_name'])


        ### implicitly search.
        if "search_value" in post_data:
            ret_data['search_value'] = post_data["search_value"]

        if not ret_data:
            return HttpResponse("ERROR: post data illegal. No query field provided.", status=400)

        return super().dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = self.prepare_post(request, field_require=False)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### Query data from db.
        if 'uuid' in data_check_result:
            queryset = BindNSRecord.objects.filter(uuid=data_check_result['uuid'],is_deleted=0)
        elif 'all_zones' in data_check_result:
            queryset = BindNSRecord.objects.filter(is_deleted=0)
        else:
            zone_belong = data_check_result.pop('zone_belong')
            queryset = BindNSRecord.objects.filter(zone_belong=zone_belong,is_deleted=0)
            if 'get_all' not in data_check_result:
                filter_dict = {'is_deleted': 0}
                for attr in ('is_applied', 'is_disabled', 'view_belong', 'record_type', 'ttl_seconds','name','resolv_addr'):
                    if attr in data_check_result:
                        filter_dict[attr] = data_check_result.pop(attr)
                queryset = queryset.filter(**filter_dict)
                if "search_value" in data_check_result:
                    search_value = data_check_result['search_value']
                    queryset = queryset.filter(Q(name__icontains = search_value) | Q(resolv_addr__icontains = search_value) | Q(description__icontains = search_value))

        ### Make query data for return.
        self.response_data['query_data'] = []
        if not queryset.exists():
            self.response_data['message'] += 'No resolv record found. '
        else:
            for obj in queryset.order_by('id'):
                if not obj.view_belong:
                    view_belong_name = 'DEFAULT'
                    view_belong_alias = '全链路解析'
                else:
                    view_belong_name = obj.view_belong.name
                    view_belong_alias = obj.view_belong.readable_name
                resolv_record = {'resolv_uuid': obj.uuid,
                              'resolv_name': obj.name,
                              'record_type': obj.record_type,
                              'resolv_addr': obj.resolv_addr,
                              'zone_belong': obj.zone_belong.name,
                              'view_belong': view_belong_name,
                              'view_belong_alias':view_belong_alias,
                              'ttl_seconds': obj.ttl_seconds,
                              'description': obj.description,
                              'add_time'   : obj.add_time.strftime('%Y-%m-%d %H:%M:%S'),
                              'is_applied' : obj.is_applied,
                              'is_disabled': obj.is_disabled,
                              }
                if dns_settings.ENABLE_MULTI_CLUSTERS:
                    resolv_record['cluster_name'] = obj.cluster_name
                    resolv_record['cluster_name_alias'] = dns_settings.CLUSTER_NAME_DEFINE.get(obj.cluster_name)
                self.response_data['query_data'].append(resolv_record)
            self.response_data['message'] += '%d resolv records found.' % len(self.response_data['query_data'])

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')


@method_decorator(csrf_exempt, name='dispatch')
class NSApiResolvApply(View, NSApiResolvCommon):
    """
    Note: this API only write file, never restart the 'named' service.
    """
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'resolv_apply',        ### Type str: 'resolv_apply' is the only value.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {}
        if "resolv_apply" in post_data and post_data['resolv_apply'] == 'resolv_apply':
            ret_data['resolv_apply'] = 'resolv_apply'
        else:
            return HttpResponse('ERROR: post data illegal.', status=400)
        return ret_data

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = super().prepare_post(request)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### write zone files.
        resolv_config_handler = BindResolvHandler()
        file_write_ret = resolv_config_handler.writeZoneFiles()
        if not isinstance(file_write_ret, dict):
            return HttpResponse(str(file_write_ret), status=400)

        ### notice slaves to apply
        if dns_settings.SLAVE_SERVER_LIST and dns_settings.THIS_IS_MASTER:
            slave_apply_result = self.notice_slaves('APPLY_RESOLV')
            print(slave_apply_result)
            if file_write_ret['named_conf_updated']:
                slave_apply_result_2 = self.notice_slaves('APPLY_NAMED_CONF')
                print(slave_apply_result_2)

        return HttpResponse(json.dumps(file_write_ret), content_type='application/json')
