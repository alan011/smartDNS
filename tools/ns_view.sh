#!/bin/bash
server_name='127.0.0.1'
port='10081'
ns_token="rs6PzzmWgxUUxXklvk7spoxHGCLOFloJ"

# add_url="http://${server_name}/dns/api/view/add"
# delete_url="http://${server_name}/dns/api/view/delete"
# modify_url="http://${server_name}/dns/api/view/modify"
# query_url="http://${server_name}/dns/api/view/query"
# apply_url="http://${server_name}/dns/api/view/apply"

if [ ! -f /usr/bin/jq ]; then
    yum install -y /usr/bin/jq
fi

agent_api_url="http://${server_name}:${port}/dns/api/agent"

function usage(){
cat << EOF
Usage:
    ./view.sh add    <view_name> <readable_name> <acl_name> <allowed_key> <description> [<cluster_name>]
    ./view.sh delete <view_name>
    ./view.sh modify <view_name> <attribute_can_be_modified>=<new_value>,...
    ./view.sh query  <some_attribute>=<search_value>,...
    ./view.sh apply

Note:
    <acl_name> must be one of: 'devsubnet', 'sitsubnet', 'uatsubnet', 'prosubnet', 'ptsubnet'.
    <allowed_key> must be one of: 'dev-key', 'sit-key','uat-key','staff-key','pro-key'.
    For query, you can use 'get_all=get_all' to get all related data.
EOF
}

function add(){
    data_str='{"action":"add","object":"view","ns_token":"'$ns_token'","view_name":"'$1'","readable_name":"'$2'","acl_name":"'$3'","allowed_key":"'$4'","description":"'$5'","cluster_name":"'$6'"}'
    # echo \'$data_str\'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function delete(){
    data_str='{"action":"delete","object":"view","ns_token":"'$ns_token'","view_name":"'$1'"}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function modify(){
    args=`echo $2 | awk -F',' '{for(i = 1; i<NF; i++){split($i, a, "="); printf "\"%s\":\"%s\",",a[1],a[2] }; split($NF, a, "="); printf "\"%s\":\"%s\"",a[1],a[2]}'`
    data_str='{"action":"modify","object":"view","ns_token":"'$ns_token'","view_name":"'$1'",'${args}'}'
    echo $data_str
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function query(){
    params="$1"
    [ -z "$params" ] && params="get_all=get_all"
    args=`echo $params | awk -F',' '{for(i = 1; i<NF; i++){split($i, a, "="); printf "\"%s\":\"%s\",",a[1],a[2] }; split($NF, a, "="); printf "\"%s\":\"%s\"",a[1],a[2]}'`
    data_str='{"action":"query","object":"view","ns_token":"'$ns_token'",'${args}'}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function apply(){
    data_str='{"action":"apply","object":"view","ns_token":"'$ns_token'","view_apply":"view_apply"}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

#---------------- main ----------

echo "$1" | egrep '^(add|delete|modify|query|apply)$' > /dev/null
[ $? -ne 0 ] && usage && exit 1

$1 "$2" "$3" "$4" "$5" "$6" "$7"
