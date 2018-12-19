import os, filecmp, shutil, re
from dns.dns_settings import (
    BIND_ZONE_FILE_ROOT, BIND_RESOLV_TEMPLATE_FILE, RECORD_TYPE_CHOICES, NS_SERVERS
)
from dns.models import BindNSRecord, BindConfigZone, BindConfigView, BindFileRegister
from dns.tools.jinja2_render import Jinja2Render

from .ns_config_common import BindConfigCommon
from .ns_base_config_handler import BindNamedConfHandler
from django.db.models import Q

class BindResolvHandler(BindConfigCommon):
    zone_file_cache = '/dev/shm/dns_file_cache'
    """
    To write a record to zone file which it belongs to.
    """
    def __init__(self):
        self.template_file   = BIND_RESOLV_TEMPLATE_FILE
        if not os.path.isdir(BIND_ZONE_FILE_ROOT):
            os.makedirs(BIND_ZONE_FILE_ROOT)
        if not os.path.isdir(self.zone_file_cache):
            os.mkdir(self.zone_file_cache)
        super().__init__()

    def getResolvDataDict(self):
        data_dict = {}
        for view_obj in self.getViewObjects():
            for zone_obj in self.getZoneObjects():
                ttl_groups = self.collectByTTL(zone_obj, view_obj)
                if ttl_groups:
                    zone_file_path = os.path.join(BIND_ZONE_FILE_ROOT, view_obj.name, '%s.%s.zone' % (zone_obj.name, view_obj.name))
                    data_dict[zone_file_path] = {
                        'zone_name' : zone_obj.name,
                        'NS_SERVERS': NS_SERVERS,
                        'ttl_groups': ttl_groups,
                    }
        return data_dict

    def collectByTTL(self, zone_obj, view_obj):
        data_filter_1 = self.data_filter.copy()
        data_filter_2 = self.data_filter.copy()
        data_filter_1.update({'is_deleted':0, "is_disabled":0, "zone_belong":zone_obj, "view_belong":view_obj})
        data_filter_2.update({'is_deleted':0, "is_disabled":0, "zone_belong":zone_obj, "view_belong":None})
        record_objs = BindNSRecord.objects.filter(Q(**data_filter_1) | Q(**data_filter_2)).order_by("name")

        tmp_data = {}
        for obj in record_objs:
            ttl_set = obj.ttl_seconds
            MX_record = None
            if obj.record_type == 'MX':
                one_record = {'resolv_name': obj.name,
                              'record_type': 'A',
                              'resolv_addr': obj.resolv_addr,
                              }
                MX_record  = {'resolv_name': '@',
                              'record_type': 'MX',
                              'resolv_addr': '10 ' + obj.name,
                              }
            else:
                one_record = {'resolv_name': obj.name,
                              'record_type': obj.record_type,
                              'resolv_addr': obj.resolv_addr,
                              }
                if one_record['record_type'] == 'CNAME':
                    if re.search('\.{}$'.format(zone_obj.name), obj.resolv_addr):
                        one_record['resolv_addr']=obj.resolv_addr[:-(len(zone_obj.name) + 1)]
                    elif not re.search('\.$',obj.resolv_addr):
                        one_record['resolv_addr'] += '.'

            if ttl_set in tmp_data:
                tmp_data[ttl_set].append(one_record)
                if MX_record:
                    tmp_data[ttl_set].append(MX_record)
            else:
                tmp_data[ttl_set] = [one_record]
                if MX_record:
                    tmp_data[ttl_set].append(MX_record)
        sorted_ttl_set = list(tmp_data.keys())
        sorted_ttl_set.sort()
        ret_data = []
        for ttl_set in sorted_ttl_set:
            t_group = {'ttl_set': ttl_set,'resolv_records': tmp_data[ttl_set]}
            ret_data.append(t_group)
        return ret_data

    def getZoneObjects(self):
        data_filter = self.data_filter.copy()
        data_filter['is_deleted'] = 0
        if 'cluster_name__in' in data_filter:
            data_filter.pop('cluster_name__in')
        return BindConfigZone.objects.filter(**data_filter)
    def getViewObjects(self):
        data_filter = self.data_filter.copy()
        data_filter['is_deleted'] = 0
        return BindConfigView.objects.filter(**data_filter)

    def getUnappliedResolvObjects(self):
        data_filter = self.data_filter.copy()
        data_filter['is_applied'] = 0
        return BindNSRecord.objects.filter(**data_filter)

    def writeZoneFiles(self):
        data_ret = {'result':'SUCCESS','changed_files':[], 'named_conf_updated':False}
        data_dict = self.getResolvDataDict()
        unapplied_data = self.getUnappliedResolvObjects()

        ### Rendering and write zone files to cache dir.
        render_fail_count = 0
        render_fail_files = []
        for file_path in data_dict:
            ### Generate cache file.
            cache_file = os.path.join(self.zone_file_cache, os.path.basename(file_path))
            result = self.render.jinjia2Render(data_dict[file_path], self.template_file, cache_file)
            if not (isinstance(result, dict) and result['result'] == 'SUCCESS'):
                render_fail_count += 1
                render_fail_files.append(os.path.basename(file_path))

        ### When rending file succeeded, To compare old zone file with new file in cache, if changed, update it.
        files_change = []
        for file_path in data_dict:
            cache_file = os.path.join(self.zone_file_cache, os.path.basename(file_path))
            if os.path.isfile(file_path):
                if not filecmp.cmp(cache_file, file_path, shallow=False):
                    files_change.append((cache_file, file_path))
            else:
                files_change.append((cache_file, file_path))

        ### to update zone files
        if files_change:
            for cache_file, file_path in files_change:
                if not os.path.isdir(os.path.dirname(file_path)):
                    os.mkdir(os.path.dirname(file_path))
                shutil.copyfile(cache_file, file_path)

        ### If zone file list changed, to update named.conf
        file_path_list = list(data_dict.keys())
        file_list_changes = self.updateZoneFileList(file_path_list)
        if file_list_changes['zone_file_deleted'] or file_list_changes['zone_file_added']:
            named_config_handler = BindNamedConfHandler()
            file_write_ret = named_config_handler.configBindNamedConf()  ### This will also trigger service reload.
            if not isinstance(file_write_ret, dict):
                return str(file_write_ret)
            data_ret['named_conf_updated'] = True
        elif files_change:   ### To reload named service, if not triggered by apply named.conf.
            op_result = self.reloadNamed()
            if op_result != 'SUCCESS':
                data_ret['result'] = "FAILED"
                data_ret['message'] = op_result

        ### If success, mark unapplied objects to be applied.
        if render_fail_count == 0:
            for obj in self.getUnappliedResolvObjects():
                obj.is_applied = 1
                obj.save()
        else:
            return "ERROR: To render file failed: %s" % ','.join(render_fail_files)

        data_ret['changed_files'] = [file_path for cache_file, file_path in files_change]
        return data_ret
