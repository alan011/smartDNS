from django.http                  import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators      import method_decorator
from django.views.generic         import View
from django.db.models import Q

from .ns_api_auth     import NSApiAuth
from .ns_api_common   import NSApiCommon
from dns              import dns_settings
from dns.models       import BindConfigZone, BindConfigView, BindNSRecord

import json, re, os


class NSApiZoneCommon(NSApiAuth, NSApiCommon):
    def dataCheckForZoneName(self,zone_name):
        if not isinstance(zone_name,str):
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'zone_name'", status=400)
        elif re.search("[^a-zA-Z0-9\.\-]", zone_name):
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'zone_name'", status=400)

        return zone_name.lower()

    def dataCheckForZoneType(self, zone_type):
        if zone_type not in [a for a,b in dns_settings.ZONE_TYPE_CHOICES]:
            return HttpResponse("ERROR: post data illegal. Illegal value for field 'zone_type'. ", status=400)
        return zone_type

@method_decorator(csrf_exempt, name='dispatch')
class NSApiZoneAdd(View, NSApiZoneCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'zone_name',        ### Type str: zone name string, re match '^[a-zA-Z0-9\.\-]*$' is required.
                    'zone_type',        ### Type str: choice from dns_settings.ZONE_TYPE_CHOICES
                    'description',      ### Type str: Any string inlcude a ''.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {"name"       : self.dataCheckForZoneName(post_data['zone_name']),
                    "zone_type"  : self.dataCheckForZoneType(post_data['zone_type']),
                    "description": str(post_data['description']),  ### 'description' field do not need to check.
                    }
        return super(NSApiZoneAdd, self).dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = super().prepare_post(request)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### write post data to db.
        zone_queryset = self.checkObjExist({'name':data_check_result['name']}, BindConfigZone)
        if zone_queryset:
            zone_obj = zone_queryset.get(name=data_check_result['name'])
            if zone_obj.is_deleted == 0:
                self.response_data['message'] += "To add a zone: zone '%s' aready existed, DB operation ignored. " % data_check_result['name']
            else:
                self.readdAnObject(zone_obj, data_check_result)
                self.response_data['message'] += "To add a zone: add zone '%s' to DB successfully. " % data_check_result['name']
        else:
            new_zone_obj = BindConfigZone(**data_check_result)
            new_zone_obj.save()
            self.response_data['message'] += "To add a zone: add zone '%s' to DB successfully. " % data_check_result['name']

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')


@method_decorator(csrf_exempt, name='dispatch')
class NSApiZoneDelete(View, NSApiZoneCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'zone_id',          ### Type int: id in DB.
                    'zone_name',        ### Type str: zone name string, re match '^[a-zA-Z0-9\.]*$' is required.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {}
        if 'zone_name' in post_data:
            ret_data["name"] = self.dataCheckForZoneName(post_data['zone_name'])
        if 'zone_id'   in post_data:
            ret_data["id"]   = int(post_data['zone_id'])
        if not ret_data:
            return HttpResponse('ERROR, field "zone_id" or "zone_name" must be provided. ', status=400)
        return super().dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = super().prepare_post(request, field_require=False)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### Write post data to db.
        zone_queryset = self.checkObjExist(data_check_result, BindConfigZone)
        print(data_check_result)
        if not zone_queryset:
            self.response_data['message'] += "To delete a zone: zone by filter '%s' not found, nothing to do. " % ','.join(["%s:%s" (key,val) for key,val in data_check_result.items()])
        else:
            zone_obj = zone_queryset.get(**data_check_result)
            if zone_obj.is_deleted:
                self.response_data['message'] += "To delete a zone: zone '%s' has already been deleted, nothing to do. " % zone_obj.name
            else:
                zone_obj.is_deleted = 1
                zone_obj.save()
                # resolv_in_zone = zone_obj.containing_records.all()
                # for resolv_obj in resolv_in_zone:
                #     resolv_obj.is_disabled = 1
                #     resolv_obj.save()
                self.response_data['message'] += "To delete a zone: delete zone '%s' successfully, please remember to apply it to service. " % zone_obj.name

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')


@method_decorator(csrf_exempt, name='dispatch')
class NSApiZoneModify(View, NSApiZoneCommon):
    """
    Only 'description' can be modified.
    """
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'zone_name',        ### Type str: zone name string, re match '^[a-zA-Z0-9\.]*$' is required.
                    'zone_type',        ### Type str: choice from dns_settings.ZONE_TYPE_CHOICES
                    'description',      ### Type str: Any string inlcude a ''.
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {'name'       : self.dataCheckForZoneName(post_data['zone_name']),
                    }
        if "zone_type" in post_data:
            ret_data['zone_type'] = self.dataCheckForZoneType(post_data['zone_type'])

        if "description" in post_data:
            ret_data["description"] = str(post_data["description"])
        return super().dataCheckInDetail(ret_data)

    def post(self, request):
        ### To do post filed checking, authentication, post data checking, and return the usable data.
        data_check_result = super().prepare_post(request, field_require=False)
        if isinstance(data_check_result, HttpResponse):
            return data_check_result

        ### Write post data to db.
        zone_queryset = self.checkObjExist({'name':data_check_result['name']}, BindConfigZone)
        if not zone_queryset:
            self.response_data['message'] += "To modify a zone: zone '%s' not exist, nothing to do. " % data_check_result['name']
            self.response_data['result'] = 'FAILED'
        else:
            zone_obj = zone_queryset.get(name=data_check_result['name'])
            if zone_obj.is_deleted == 1:
                self.response_data['message'] += "To modify a zone: zone '%s' has been deleted yet, nothing to do. " % data_check_result['name']
                self.response_data['result'] = 'FAILED'
            else:
                if 'zone_type' in data_check_result:
                    zone_obj.zone_type = data_check_result['zone_type']
                if 'description' in data_check_result:
                    zone_obj.description = data_check_result['description']
                zone_obj.save()
                self.response_data['message'] += "To modify a zone: modify zone '%s' successfully. " % data_check_result['name']

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')

@method_decorator(csrf_exempt, name='dispatch')
class NSApiZoneQuery(View, NSApiZoneCommon):
    legal_fields = ['ns_token',         ### Type str: A 32-length-string
                    'get_all',          ### Type str: 'get_all' is the only value.
                    'zone_id',          ### Type int: for explicitely search as a filter.
                    'zone_name',        ### Type str: for explicitely search as a filter.
                    'zone_type',        ### Type str: choice from dns_settings.ZONE_TYPE_CHOICES
                    'search_value'      ### Type str: search value to match field 'zone_name' or 'description'
                   ]
    def dataCheckInDetail(self, post_data):
        ret_data = {}
        if 'get_all'     in post_data:
            if post_data['get_all'] == 'get_all':
                ret_data['get_all'] = 'get_all'
                return ret_data
            else:
                return HttpResponse("ERROR: post data illegal. Illegal value for field 'get_all'", status=400)
        elif "zone_id"   in post_data:
            ret_data['id'] = int(post_data["zone_id"])
            return ret_data
        elif "zone_name"   in post_data:
            ret_data['name']   = str(post_data['zone_name']).strip()
            return ret_data

        if "zone_type"   in post_data:
            ret_data["zone_type"]   = self.dataCheckForZoneType(post_data['zone_type'])
        if "search_value" in post_data:
            ret_data["search_value"] = str(post_data["search_value"])
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
            queryset = BindConfigZone.objects.filter(is_deleted=0)
        elif 'id'  in data_check_result:
            queryset =  BindConfigZone.objects.filter(id=data_check_result['id'],is_deleted=0)
        elif 'name' in data_check_result:
            queryset =  BindConfigZone.objects.filter(name=data_check_result['name'],is_deleted=0)
        else:
            filter_dict = {'is_deleted': 0}
            if 'zone_type' in data_check_result:
                filter_dict['zone_type'] = data_check_result.pop('zone_type')
            queryset = BindConfigZone.objects.filter(**filter_dict)
            if 'search_value' in data_check_result:
                search_value = data_check_result.pop('search_value')
                queryset = queryset.filter(Q(name__icontains = search_value) | Q(description__icontains = search_value))

        ### Make query data for return.
        self.response_data['query_data'] = []
        if not queryset.exists():
            self.response_data['message'] += 'No zone found. '
        else:
            for obj in queryset.order_by('id'):
                zone_found = {'id'    : obj.id,
                              'zone_name'  : obj.name,
                              'zone_type'  : obj.zone_type,
                              'description': obj.description,
                              'add_time'   : obj.add_time.strftime('%Y-%m-%d %H:%M:%S'),
                              'containing_records':obj.containing_records.filter(is_deleted=0).count(),
                              }
                self.response_data['query_data'].append(zone_found)
            self.response_data['message'] += '%d zones found.' % len(self.response_data['query_data'])

        return HttpResponse(json.dumps(self.response_data), content_type='application/json')
