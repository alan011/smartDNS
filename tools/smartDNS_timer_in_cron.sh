#!/bin/bash

BASE_DIR="/var/django_projects/dns/smartDNS"
TOOL_DIR="${BASE_DIR}/tools"
TIMER_LOG_DIR="${BASE_DIR}/timer_log"
TIMER_LOG_FILE="${TIMER_LOG_DIR}/timer.log.`date +'%Y%m%d'`"

function prepare() {
    if [ ! -d $TIMER_LOG_DIR ]; then
        mkdir -p $TIMER_LOG_DIR
    fi
    check_pid_count=`ps -ef | grep smartDNS_timer_in_cron.sh | grep -v grep | grep -v $$ | wc -l`
    if [ $check_pid_count -gt 0 ]; then
        echo "`date +'%Y-%m-%d %H:%M:%S'` [WARNING] Another progress is running, this job will be aborted this time." >> $TIMER_LOG_FILE
        exit 0
    fi
}

function apply_resolv_data() {
    echo "`date +'%Y-%m-%d %H:%M:%S'` [INFO] To run 'ns_apply.sh resolv': " >> $TIMER_LOG_FILE
    /bin/bash /var/django_projects/dns/smartDNS/tools/ns_apply.sh resolv >> $TIMER_LOG_FILE 2>&1
    echo >> $TIMER_LOG_FILE
}

function re_sync_failed_data() {
    echo "`date +'%Y-%m-%d %H:%M:%S'` [INFO] To run 'sync_data_in_cache.py': " >> $TIMER_LOG_FILE
    /usr/bin/python3 ${TOOL_DIR}/sync_data_in_cache.py >> $TIMER_LOG_FILE 2>&1
}

function clean_log(){
    find $TIMER_LOG_DIR -ctime +30 -name "timer.log*" -delete
}

#-------------------- main ----------------
prepare
apply_resolv_data
re_sync_failed_data
clean_log
