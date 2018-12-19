#!/bin/bash
base_dir="/var/django_projects/dns/smartDNS/tools"

function usage(){
cat << EOF
Usage:
    ./ns_apply.sh iplist|view|resolv|ALL

EOF
}


#---------------- main ----------

echo "$1" | egrep '^(iplist|view|resolv|ALL)$' > /dev/null
[ $? -ne 0 ] && usage && exit 1

cd $base_dir
if [ "$1" == "ALL" ]; then
    ./ns_iplist.sh apply
    ./ns_view.sh apply
    ./ns_resolv.sh apply
else
    ./ns_${1}.sh apply
fi
