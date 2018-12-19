import os
from dns.models import BindNSRecord, BindFileRegister
from dns.ns_factory.ns_service_manager import ServiceManager
from dns import dns_settings
from dns.tools import Jinja2Render

class BindConfigCommon(object):
    def __init__(self):
        self.data_filter   = self.getMultiClusterDataFilter()
        self.render        = Jinja2Render()

    def getMultiClusterDataFilter(self):
        data_filter = {}
        if dns_settings.ENABLE_MULTI_CLUSTERS == True:
            data_filter['cluster_name__in'] = [dns_settings.THIS_CLUSTER_NAME, 'ALL']
        return data_filter

    def reloadNamed(self, to_reload=dns_settings.SERVICE_RELOAD):
        service_manager = ServiceManager()
        if to_reload:
            operation = 'reload'
        else:
            operation = 'restart'
        return service_manager.serviceOperate(operation)

    def updateZoneFileList(self,file_path_list):
        zone_file_queryset = BindFileRegister.objects.filter(file_type=0, is_deleted=0)
        old_zone_file_list = [ obj.file_path for obj in zone_file_queryset ]
        to_delete_files = [ f for f in old_zone_file_list if f not in file_path_list ]
        to_add_files    = [ f for f in file_path_list if f not in old_zone_file_list ]

        for obj in zone_file_queryset:
            if obj.file_path in to_delete_files:
                obj.is_deleted = 1
                obj.save()

        for file_path in to_add_files:
            delete_queryset = BindFileRegister.objects.filter(file_path=file_path)
            if delete_queryset.exists():
                file_obj = delete_queryset.get(file_path=file_path)
                file_obj.is_deleted = 0
                file_obj.file_type = 0
            else:
                file_obj = BindFileRegister(file_path=file_path, file_type=0)
            file_obj.save()

        return {'zone_file_deleted':to_delete_files, 'zone_file_added': to_add_files}
