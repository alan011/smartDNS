#!/bin/bash
server_name='127.0.0.1'
port='10081'
ns_token="rs6PzzmWgxUUxXklvk7spoxHGCLOFloJ"

# add_url="http://${server_name}/dns/api/zone/add"
# delete_url="http://${server_name}/dns/api/zone/delete"
# modify_url="http://${server_name}/dns/api/zone/modify"
# query_url="http://${server_name}/dns/api/zone/query"


if [ ! -f /usr/bin/jq ]; then
    yum install -y /usr/bin/jq
fi

agent_api_url="http://${server_name}:${port}/dns/api/agent"

function usage(){
cat << EOF
Usage:
    ./iplist_mng.sh add    <zone_name> <zone_type> <description>
    ./iplist_mng.sh delete <zone_name>
    ./iplist_mng.sh modify <zone_name> <attribute_can_be_modified>=<new_value>,...
    ./iplist_mng.sh query  <some_attribute>=<search_value>,...

Note:
    For query, you can use 'get_all=get_all' to get all related data.
EOF
}

function add(){
    data_str='{"action":"add","object":"zone","ns_token":"'$ns_token'","zone_name":"'$1'","zone_type":"'$2'","description":"'$3'"}'
    # echo \'$data_str\'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
    # echo curl -s $add_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\'
}

function delete(){
    data_str='{"action":"delete","object":"zone","ns_token":"'$ns_token'","zone_name":"'$1'"}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function modify(){
    args=`echo $2 | awk -F',' '{for(i = 1; i<NF; i++){split($i, a, "="); printf "\"%s\":\"%s\",",a[1],a[2] }; split($NF, a, "="); printf "\"%s\":\"%s\"",a[1],a[2]}'`
    data_str='{"action":"modify","object":"zone","ns_token":"'$ns_token'","zone_name":"'$1'",'${args}'}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function query(){
    params="$1"
    [ -z "$params" ] && params="get_all=get_all"
    args=`echo $params | awk -F',' '{for(i = 1; i<NF; i++){split($i, a, "="); printf "\"%s\":\"%s\",",a[1],a[2] }; split($NF, a, "="); printf "\"%s\":\"%s\"",a[1],a[2]}'`
    data_str='{"action":"query","object":"zone","ns_token":"'$ns_token'",'${args}'}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

#---------------- main ----------

echo "$1" | egrep '^(add|delete|modify|query)$' > /dev/null
[ $? -ne 0 ] && usage && exit 1

$1 "$2" "$3" "$4"
