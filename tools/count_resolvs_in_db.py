#!/usr/local/bin/python3
import os, sys, re, time, json, django

sys.path.append('/var/django_projects/dns/smartDNS/dns_project')
#os.environ['DJANGO_SETTING_MODULE']='geniusalt_project.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dns_project.settings")
django.setup()


from dns.models import BindConfigACL, BindConfigView, BindConfigZone, BindNSRecord
from dns.ns_api.ns_api_common import APICaller
from dns import dns_settings


#---------------- main --------------
if __name__ == '__main__':
    for obj in BindNSRecord.objects.filter(is_deleted = 0, is_disabled = 0, cluster_name__in = [ sys.argv[1], 'ALL'] ).order_by('name'):
        print("%s %s %s" % (obj.name, obj.record_type, obj.resolv_addr))
        

