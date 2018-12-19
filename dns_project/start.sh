#!/bin/bash

#export PYTHONUNBUFFERED=1

cd /var/django_projects/dns/smartDNS/dns_project/

python3 manage.py runserver 0.0.0.0:10081
