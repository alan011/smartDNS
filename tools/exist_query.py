#!/usr/local/bin/python3

import json, sys, re, os

f = open(sys.argv[1])
while True:
    line=f.readline()
    if not line:
        break
    print("\n====> query for '%s':" % line.strip())
    full_name   = line.split()[0].strip()
    resolv_addr = line.split()[1].strip()
    zone_name   = '.'.join(full_name.split('.')[-2:])
    if re.search('\.hf$',full_name):
        zone_name = 'hf'
    elif re.search('\.com.cn$',full_name):
        zone_name = '.'.join(full_name.split('.')[-3:])
    resolv_name = full_name.replace('.' + zone_name, '')

    data_f = os.popen('/var/django_projects/dns/smartDNS/tools/ns_resolv.sh query zone_name=%s,resolv_name=%s' % (zone_name, resolv_name))
    data   = data_f.read()
    print(data)
    if re.search('^ERROR:', data):
        print(data)
        continue
    data_dict=json.loads(data)
    records_found = data_dict['query_data']
    addr_list=[]
    for rec in records_found:
        addr_list.append(rec['resolv_addr'].strip())
        print("%s:  %s.%s  %s  %s" % (rec['view_belong'], rec['resolv_name'], rec['zone_belong'],rec['record_type'],rec['resolv_addr'] ))
    if resolv_addr not in addr_list:
        print("ERROR: %s->%s not found in query data." % (full_name, resolv_addr))
    
     

