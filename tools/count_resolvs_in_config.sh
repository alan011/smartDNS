#!/bin/bash


count=0
for f in `cat /etc/named.conf | grep 'file "/var/named/named.mbank.zones/' | awk -F'"' '{print $2}'`; do
    cat $f | egrep '[[:blank:]]+A[[:blank:]]+' | while read line; do 
        echo $line
        count=$(( count + 1 ))
    done
done


#echo -e "\n ====> $count A records are found."
