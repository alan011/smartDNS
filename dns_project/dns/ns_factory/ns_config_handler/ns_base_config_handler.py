import os
from dns.dns_settings import (
    BIND_ACL_CONFIG_TEMPLATE_FILE, BIND_ACL_CONFIG_TARGET_FILE, BIND_MAIN_CONFIG_TEMPLATE_FILE,
    BIND_MAIN_CONFIG_TARGET_FILE, ACL_NAME_DEFINE, VIEW_KEY_DEFINE, BIND_ZONE_FILE_ROOT,
)
from dns.models import BindConfigACL, BindConfigView, BindNSRecord
from dns.tools.jinja2_render import Jinja2Render
from django.db.models import Q

from .ns_config_common import BindConfigCommon

class BindACLConfigHandler(BindConfigCommon):
    """
    To get data from db, and write ACL config file for Bind9. Do not restart the 'named' service.
    The 'service_manager' will handle with the restart work.
    """
    def __init__(self):
        self.template_file = BIND_ACL_CONFIG_TEMPLATE_FILE
        self.target_file   = BIND_ACL_CONFIG_TARGET_FILE
        super().__init__()

    def getACLDict(self):
        acl_dict = {acl_name:[] for acl_name, alias_name in ACL_NAME_DEFINE }
        for acl_name in acl_dict:
            data_filter = self.data_filter.copy()
            data_filter.update({'acl_name':acl_name, 'is_deleted':0})
            subnet_objs = BindConfigACL.objects.filter(**data_filter)
            for obj in subnet_objs:
                acl_dict[acl_name].append(obj.subnet)
        return acl_dict

    def getUnappliedSubnet(self):
        data_filter = self.data_filter.copy()
        data_filter.update({'is_applied':0})
        return BindConfigACL.objects.filter(**data_filter)

    def configBindACL(self):
        acl_dict          = self.getACLDict()
        unapplied_sunbets = self.getUnappliedSubnet()

        ### Rendering and write the ACL config file.
        data_ret = self.render.jinjia2Render({'acl_dict':acl_dict}, self.template_file,  self.target_file)

        ### If success, to set acl subnet objs's attribute 'is_applied' to 1 .
        if isinstance(data_ret, dict) and data_ret['result'] == 'SUCCESS':
            for obj in unapplied_sunbets:
                obj.is_applied = 1
                obj.save()
            ### To reload service named
            op_result = self.reloadNamed()
            if op_result != 'SUCCESS':
                data_ret['result'] = "FAILED"
                data_ret['message'] = op_result

        return data_ret

class BindNamedConfHandler(BindConfigCommon):
    """
    To config bind main config file: named.conf.
    """
    def __init__(self):
        self.template_file   = BIND_MAIN_CONFIG_TEMPLATE_FILE
        self.target_file     = BIND_MAIN_CONFIG_TARGET_FILE
        super().__init__()

    def getZonesByView(self, view_obj):
        zones_find = {}
        data_filter_1 = self.data_filter.copy()
        data_filter_2 = self.data_filter.copy()
        data_filter_1.update({"is_deleted":0, "is_disabled":0, "view_belong":view_obj})
        data_filter_2.update({"is_deleted":0, "is_disabled":0, "view_belong":None})
        record_queryset = BindNSRecord.objects.filter(Q(**data_filter_1) | Q(**data_filter_2)).order_by("name")
        for record_obj in record_queryset:
            zone_obj = record_obj.zone_belong
            if zone_obj.is_deleted == 0 and zone_obj.name not in zones_find:
                zones_find[zone_obj.name] = {"name":zone_obj.name, "file_path":os.path.join(BIND_ZONE_FILE_ROOT, view_obj.name, '%s.%s.zone' % (zone_obj.name,view_obj.name))}
        return list(zones_find.values())

    def getViewDataDict(self):
        data_dict = {'view_config_list':[],
                    'key_list'         :list(VIEW_KEY_DEFINE.items()),
                    "acl_config_file"  :BIND_ACL_CONFIG_TARGET_FILE,
                    }
        data_dict['key_list'].sort()

        data_filter = self.data_filter.copy()
        data_filter.update({'is_deleted':0})
        queryset  = BindConfigView.objects.filter(**data_filter)
        for obj in queryset:
            a_view = {"name"       : obj.name,
                      "allowed_key": obj.allowed_key,
                      "acl_name"   : obj.acl_name,
                      "denied_keys": [key_name for key_name in VIEW_KEY_DEFINE if key_name != obj.allowed_key],
                      "zones"      : self.getZonesByView(obj),
                      }
            data_dict['view_config_list'].append(a_view)
        return data_dict

    def getUnappliedViewData(self):
        data_filter = self.data_filter.copy()
        data_filter.update({'is_applied':0})
        return BindConfigView.objects.filter(**data_filter)

    def configBindNamedConf(self):
        data_dict = self.getViewDataDict()
        unapplied_data = self.getUnappliedViewData()

        ### Rendering and write the main configure file: named.conf.
        data_ret = self.render.jinjia2Render(data_dict, self.template_file, self.target_file)

        ### If success, to set unapplied objs' attribute 'is_applied' to 1.
        if isinstance(data_ret, dict) and data_ret['result'] == 'SUCCESS':
            for obj in unapplied_data:
                obj.is_applied = 1
                obj.save()
            ### To reload service named
            op_result = self.reloadNamed()
            if op_result != 'SUCCESS':
                data_ret['result'] = "FAILED"
                data_ret['message'] = op_result

        return data_ret
