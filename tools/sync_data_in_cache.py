#!/usr/local/bin/python3
import os, sys, re, time, json, django

sys.path.append('/var/django_projects/dns/smartDNS/dns_project')
#os.environ['DJANGO_SETTING_MODULE']='geniusalt_project.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dns_project.settings")
django.setup()


from dns.models import MultiClustersDataSyncCache
from dns.ns_api.ns_api_common import APICaller
from dns import dns_settings

def sync_data(sync_all=False):
    if sync_all:
        queryset = MultiClustersDataSyncCache.objects.filter(is_synced=0).order_by('id')
    else:
        queryset = MultiClustersDataSyncCache.objects.filter(is_synced=0, retry_count__lt = 15).order_by('id')

    api_caller = APICaller()
    for obj in queryset:
        if not sync_all:
            obj.retry_count += 1
            obj.save()

        try:
            data_content = json.loads(obj.data_content)
        except:
            print("ERROR: json.loads(obj.data_content) error for object ID: %d, cluster_name: '%s'" % (obj.id, obj.failed_cluster))
        else:
            call_ret = api_caller.post_caller(obj.sync_url, post_data=data_content)
            failed_tag = 0
            if isinstance(call_ret, dict):
                if call_ret['result'] == 'SUCCESS':
                    obj.is_synced = 1
                    obj.save()
                    print("INFO: To sync data succeeded, cluster: '%s', cache id: '%d', retry count: '%d'" % (obj.failed_cluster, obj.id, obj.retry_count))
                else:
                    print("ERROR: To sync data Failed, cluster: '%s', cache id: '%d', retry count: '%d'" % (obj.failed_cluster, obj.id, obj.retry_count))
                    print("SYNC_FAILED_MESSAGE: %s" % call_ret['message'])
                    failed_tag += 1
            else:
                failed_tag += 1
                print("ERROR: To sync data returned unexpected result, cluster: '%s', cache id: '%d', retry count: '%d'" % (obj.failed_cluster, obj.id, obj.retry_count))
                print("SYNC_FAILED_UNEXPECTED_CONTENT: %s" % str(call_ret))

#---------------- main --------------
if __name__ == '__main__':
    if len(sys.argv) == 1:
        sync_data()
    elif sys.argv[1] == '--manually' :
        sync_data(sync_all=True)
