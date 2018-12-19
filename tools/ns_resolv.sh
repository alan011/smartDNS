#!/bin/bash
server_name='127.0.0.1'
port='10081'
ns_token="rs6PzzmWgxUUxXklvk7spoxHGCLOFloJ"

DEFAULT_ZONE="shishike.com"

# add_url="http://${server_name}/dns/api/resolv/add"
# delete_url="http://${server_name}/dns/api/resolv/delete"
# modify_url="http://${server_name}/dns/api/resolv/modify"
# query_url="http://${server_name}/dns/api/resolv/query"
# apply_url="http://${server_name}/dns/api/resolv/apply"

if [ ! -f /usr/bin/jq ]; then
    yum install -y /usr/bin/jq
fi

agent_api_url="http://${server_name}:${port}/dns/api/agent"

function usage(){
cat << EOF
Usage:
    ./resolv.sh add    <resolv_name> <record_type> <resolv_addr> <zone_belong> <view_belong> <ttl_seconds> <description> [<cluster_name>]
    ./resolv.sh delete <resolv_uuid>
    ./resolv.sh modify <resolv_uuid> <attribute_can_be_modified>=<new_value>,...
    ./resolv.sh query  <some_attribute>=<search_value>,...
    ./resolv.sh apply

Note:
    <record_type> must be one of: 'A', 'AAAA', 'CNAME', 'MX'.
    <ttl_seconds> must be one of: 600, 3600, 86400.
    For query, you can use 'all_zones=all_zones' to get all resolv data in all zones.
EOF
}

function add(){
    data_str='{"action":"add","object":"resolv","ns_token":"'$ns_token'","resolv_name":"'$1'","record_type":"'$2'","resolv_addr":"'$3'","zone_belong":"'$4'","view_belong":"'$5'","ttl_seconds":'$6',"description":"'$7'","cluster_name":"'$8'"}'
    echo \'$data_str\'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function delete(){
    data_str='{"action":"delete","object":"resolv","ns_token":"'$ns_token'","resolv_uuid":"'$1'"}'
    echo $data_str
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function modify(){
    args=`echo $2 | awk -F',' '{for(i = 1; i<NF; i++){split($i, a, "="); if(a[1] == "is_disabled"){printf "\"%s\":%s,",a[1],a[2]}else{ printf "\"%s\":\"%s\",",a[1],a[2] } }; split($NF, a, "=");if(a[1] == "is_disabled"){printf "\"%s\":%s",a[1],a[2]} else {printf "\"%s\":\"%s\"",a[1],a[2]} }'`
    data_str='{"action":"modify","object":"resolv","ns_token":"'$ns_token'","resolv_uuid":"'$1'",'${args}'}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function query(){
    params="$1"
    [ -z "$params" ] && params="zone_name=${DEFAULT_ZONE},get_all=get_all"
    args=`echo $params | awk -F',' '{for(i = 1; i<NF; i++){split($i, a, "="); printf "\"%s\":\"%s\",",a[1],a[2] }; split($NF, a, "="); printf "\"%s\":\"%s\"",a[1],a[2]}'`
    data_str='{"action":"query","object":"resolv","ns_token":"'$ns_token'",'${args}'}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function apply(){
    data_str='{"action":"apply","object":"resolv","ns_token":"'$ns_token'","resolv_apply":"resolv_apply"}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

#---------------- main ----------

echo "$1" | egrep '^(add|delete|modify|query|apply)$' > /dev/null
[ $? -ne 0 ] && usage && exit 1

$1 "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9"
