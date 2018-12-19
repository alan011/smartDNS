#!/bin/bash
server_name='127.0.0.1'
port='10081'
ns_token="rs6PzzmWgxUUxXklvk7spoxHGCLOFloJ"

# add_url="http://${server_name}/dns/api/acl/add"
# delete_url="http://${server_name}/dns/api/acl/delete"
# modify_url="http://${server_name}/dns/api/acl/modify"
# query_url="http://${server_name}/dns/api/acl/query"
# apply_url="http://${server_name}/dns/api/acl/apply"
if [ ! -f /usr/bin/jq ]; then
    yum install -y /usr/bin/jq
fi

agent_api_url="http://${server_name}:${port}/dns/api/agent"

function usage(){
cat << EOF
Usage:
    ./ns_iplist.sh add    <acl_subnet> <acl_name> <description> [<cluster_name>]
    ./ns_iplist.sh delete <acl_subnet>
    ./ns_iplist.sh modify <acl_subnet> <attribute_can_be_modified>=<new_value>,...
    ./ns_iplist.sh query  <some_attribute>=<search_value>,...
    ./ns_iplist.sh apply

Note:
    <acl_name> must be one of: 'devsubnet', 'sitsubnet', 'uatsubnet', 'prosubnet', 'ptsubnet'.
    For query, you can use 'get_all=get_all' to get all acl related data.
EOF
}

function add(){
    data_str='{"action":"add","object":"iplist","ns_token":"'$ns_token'","acl_subnet":"'$1'","acl_name":"'$2'","description":"'$3'","cluster_name":"'$4'"}'
    # echo \'$data_str\'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function delete(){
    data_str='{"action":"delete","object":"iplist","ns_token":"'$ns_token'","acl_subnet":"'$1'"}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function modify(){
    args=`echo $2 | awk -F',' '{for(i = 1; i<NF; i++){split($i, a, "="); printf "\"%s\":\"%s\",",a[1],a[2] }; split($NF, a, "="); printf "\"%s\":\"%s\"",a[1],a[2]}'`
    data_str='{"action":"modify","object":"iplist","ns_token":"'$ns_token'","acl_subnet":"'$1'",'${args}'}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function query(){
    params="$1"
    [ -z "$params" ] && params="get_all=get_all"
    args=`echo $params | awk -F',' '{for(i = 1; i<NF; i++){split($i, a, "="); printf "\"%s\":\"%s\",",a[1],a[2] }; split($NF, a, "="); printf "\"%s\":\"%s\"",a[1],a[2]}'`
    data_str='{"action":"query","object":"iplist","ns_token":"'$ns_token'",'${args}'}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

function apply(){
    data_str='{"action":"apply","object":"iplist","ns_token":"'$ns_token'","acl_apply":"acl_apply"}'
    echo curl -s $agent_api_url -X POST -H \'Content-Type: Application/json\' -d \'$data_str\' | sh | jq .
}

#---------------- main ----------

echo "$1" | egrep '^(add|delete|modify|query|apply)$' > /dev/null
[ $? -ne 0 ] && usage && exit 1

$1 "$2" "$3" "$4" "$5"
