#!/usr/local/bin/python3
import os, sys, re, time, json, django

sys.path.append('/var/django_projects/dns/smartDNS/dns_project')
#os.environ['DJANGO_SETTING_MODULE']='geniusalt_project.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dns_project.settings")
django.setup()


from dns.models import BindConfigACL, BindConfigView, BindConfigZone, BindNSRecord
from dns.ns_api.ns_api_common import APICaller
from dns import dns_settings

def checkSettings():
    if not getattr(dns_settings, 'ENABLE_MULTI_CLUSTERS'):
        print("ERROR: Multi-cluster feature is not enabled.\n")
        sys.exit(1)
    if not getattr(dns_settings, "MAIN_CLUSTER_MASTER"):
        print("ERROR: Multi-cluster feature is not configured properly.")
        sys.exit(1)

def checkDataMyself():
    iplist_queryset = BindConfigACL.objects.all()
    view_queryset   = BindConfigView.objects.all()
    zone_queryset   = BindConfigZone.objects.all()
    resolv_queryset = BindNSRecord.objects.all()
    error_message = ''
    if iplist_queryset.exists():
        error_message += 'BindConfigACL: %d objects found.\n' % iplist_queryset.count()
    if view_queryset.exists():
        error_message += 'BindConfigView: %d objects found.\n' % view_queryset.count()
    if zone_queryset.exists():
        error_message += 'BindConfigZone: %d objects found.\n' % zone_queryset.count()
    if resolv_queryset.exists():
        error_message += 'BindNSRecord: %d objects found.\n' % resolv_queryset.count()

    if error_message:
        print('ERROR: Some data found in this cluster, the sync-work is aborted, please clean any data in this cluster first:\n%s' % error_message )
        sys.exit(1)

def syncIPListData(main_cluster_ip):
    print("\n==== Sync IPList data...")
    api_caller = APICaller()
    post_data = {'ns_token':'rs6PzzmWgxUUxXklvk7spoxHGCLOFloJ', 'action':'query','object':'iplist','get_all':'get_all'}
    data_ret = api_caller.post_caller("http://%s/dns/api/agent" % main_cluster_ip, post_data)
    if isinstance(data_ret, dict):
        print("All IPList data has been successfully fetched!\nNow write data to local db... ")
        count = 0
        for data_dict in data_ret['query_data']:
            data_to_write = {'subnet':data_dict['acl_subnet'],
                            'acl_name':data_dict['acl_name'],
                            'description':data_dict['description'],
                            'add_time':data_dict['add_time'],
                            'cluster_name':data_dict['cluster_name'],
                            }
            new_obj = BindConfigACL(**data_to_write)
            new_obj.save()
            count += 1
        print("%d entries of view data written succcessfully." % count)
    else:
        if re.search('^ERROR', str(data_ret)):
            print(str(data_ret))
            sys.exit(1)
        else:
            print(str(data_ret))

def syncViewData(main_cluster_ip):
    print("\n==== Sync view data...")
    api_caller = APICaller()
    post_data = {'ns_token':'rs6PzzmWgxUUxXklvk7spoxHGCLOFloJ', 'action':'query','object':'view','get_all':'get_all'}
    data_ret = api_caller.post_caller("http://%s/dns/api/agent" % main_cluster_ip, post_data)
    if isinstance(data_ret, dict):
        print("All view data has been successfully fetched!\nNow write data to local db... ")
        count = 0
        for data_dict in data_ret['query_data']:
            data_to_write = {'name':data_dict['view_name'],
                            'readable_name':data_dict['readable_name'],
                            'acl_name':data_dict['acl_name'],
                            'allowed_key':data_dict['allowed_key'],
                            'description':data_dict['description'],
                            'add_time':data_dict['add_time'],
                            'cluster_name':data_dict['cluster_name'],
                            }
            new_obj = BindConfigView(**data_to_write)
            new_obj.save()
            count += 1
        print("%d entries of view data written succcessfully." % count)
    else:
        if re.search('^ERROR', str(data_ret)):
            print(str(data_ret))
            sys.exit(1)
        else:
            print(str(data_ret))

def syncZoneData(main_cluster_ip):
    print("\n==== Sync zone data...")
    api_caller = APICaller()
    post_data = {'ns_token':'rs6PzzmWgxUUxXklvk7spoxHGCLOFloJ', 'action':'query','object':'zone','get_all':'get_all'}
    data_ret = api_caller.post_caller("http://%s/dns/api/agent" % main_cluster_ip, post_data)
    if isinstance(data_ret, dict):
        print("All zone data has been successfully fetched!\nNow write data to local db... ")
        count = 0
        for data_dict in data_ret['query_data']:
            data_to_write = {'name':data_dict['zone_name'],
                            'zone_type':data_dict['zone_type'],
                            'description':data_dict['description'],
                            'add_time':data_dict['add_time'],
                            }
            new_obj = BindConfigZone(**data_to_write)
            new_obj.save()
            count += 1
        print("%d entries of zone data written succcessfully." % count)
    else:
        if re.search('^ERROR', str(data_ret)):
            print(str(data_ret))
            sys.exit(1)
        else:
            print(str(data_ret))

def syncResolvData(main_cluster_ip):
    print("\n==== Sync resolv data...")
    api_caller = APICaller()
    post_data = {'ns_token':'rs6PzzmWgxUUxXklvk7spoxHGCLOFloJ', 'action':'query','object':'resolv','all_zones':'all_zones'}
    data_ret = api_caller.post_caller("http://%s/dns/api/agent" % main_cluster_ip, post_data)
    if isinstance(data_ret, dict):
        print("All resolv data has been successfully fetched!\nNow write data to local db... ")
        count = 0
        for data_dict in data_ret['query_data']:
            view_obj = None
            if data_dict['view_belong'] != 'DEFAULT':
                view_obj = BindConfigView.objects.get(name=data_dict['view_belong'])
            zone_obj = BindConfigZone.objects.get(name=data_dict['zone_belong'])
            data_to_write = {'uuid':data_dict['resolv_uuid'],
                            'name':data_dict['resolv_name'],
                            'record_type':data_dict['record_type'],
                            'resolv_addr':data_dict['resolv_addr'],
                            'zone_belong':zone_obj,
                            'view_belong':view_obj,
                            'ttl_seconds':data_dict['ttl_seconds'],
                            'description':data_dict['description'],
                            'add_time':data_dict['add_time'],
                            'is_disabled':data_dict['is_disabled'],
                            'cluster_name':data_dict['cluster_name'],
                            }
            new_obj = BindNSRecord(**data_to_write)
            new_obj.save()
            count += 1
        print("%d entries of resolv data written succcessfully." % count)
    else:
        if re.search('^ERROR', str(data_ret)):
            print(str(data_ret))
            sys.exit(1)
        else:
            print(str(data_ret))

def syncData():
    checkSettings()
    checkDataMyself()
    if not getattr(dns_settings, 'MAIN_CLUSTER_MASTER'):
        print('ERROR: "MAIN_CLUSTER_MASTER" is not set properly.')
    main_cluster_address = dns_settings.MAIN_CLUSTER_MASTER[1]
    syncIPListData(main_cluster_address)
    syncViewData(main_cluster_address)
    syncZoneData(main_cluster_address)
    syncResolvData(main_cluster_address)

    print('\nFinished.')


#----------------------------

syncData()
