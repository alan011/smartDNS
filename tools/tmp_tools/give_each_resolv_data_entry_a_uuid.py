#!/usr/local/bin/python3
import os, sys, re, time, json, django, random

sys.path.append('/var/django_projects/dns/smartDNS/dns_project')
#os.environ['DJANGO_SETTING_MODULE']='geniusalt_project.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dns_project.settings")
django.setup()


from dns.models import BindConfigACL, BindConfigView, BindConfigZone, BindNSRecord
from dns.ns_api.ns_api_common import APICaller
from dns import dns_settings


def genUUID(length=64):
    seed = '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''.join([ seed[random.randint(0,len(seed) - 1)] for i in range(length)])

#----------------- main -------------
if __name__ == '__main__':
    for obj in BindNSRecord.objects.all().order_by('id'):
        if len(str(obj.uuid)) != 64:
            print("====> setting id: %d" % obj.id)
            while True:
                uuid = genUUID()
                print(uuid)
                if not BindNSRecord.objects.filter(uuid=uuid).exists():
                    obj.uuid = uuid
                    obj.save()
                    break
                else:
                    print('\n\n\n')
                    continue

    print("\nFinished.")
