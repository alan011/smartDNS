#!/usr/local/bin/python3
import os, sys, re, time, json, django, random

sys.path.append('/var/django_projects/dns/smartDNS/dns_project')
#os.environ['DJANGO_SETTING_MODULE']='geniusalt_project.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dns_project.settings")
django.setup()


from dns.models import BindConfigACL, BindConfigView, BindNSRecord
from dns.ns_api.ns_api_common import APICaller
from dns import dns_settings


def checkConfig(cluster_name):
    if getattr(dns_settings, "CLUSTER_NAME_DEFINE") and cluster_name in dns_settings.CLUSTER_NAME_DEFINE:
        return True
    return False

def setAllIPListData(cluster_name):
    print("\n====> Setting iplist data... ")
    queryset = BindConfigACL.objects.all()
    count = 0
    for obj in queryset:
        obj.cluster_name = cluster_name
        obj.save()
        count += 1
    print("%d data entries are successfully updated. " % count)


def setAllViewData(cluster_name):
    print("\n====> Setting view data... ")
    queryset = BindConfigView.objects.all()
    count = 0
    for obj in queryset:
        obj.cluster_name = cluster_name
        obj.save()
        count += 1
    print("%d data entries are successfully updated. " % count)

def setAllResolvData(cluster_name):
    print("\n====> Setting resolv data... ")
    queryset = BindNSRecord.objects.all()
    count = 0
    for obj in queryset:
        obj.cluster_name = cluster_name
        obj.save()
        count += 1
    print("%d data entries are successfully updated. " % count)


#-------------------- main -------------------

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: %s <cluster_name>" % sys.argv[0])
        sys.exit(1)
    cluster_name_input = sys.argv[1]
    if checkConfig(cluster_name_input):
        setAllIPListData(cluster_name_input)
        setAllViewData(cluster_name_input)
        setAllResolvData(cluster_name_input)
        print("\nFinished.")
    else:
        print("ERROR: cluster_name input must be in %s" % str(list(dns_settings.CLUSTER_NAME_DEFINE.keys())))
        sys.exit(1)
