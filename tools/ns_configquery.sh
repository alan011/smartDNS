#!/bin/bash
server_name='127.0.0.1'
port='10080'
ns_token="e01pdXVV7kaOykULCEGHNbv4DnMObrOO"

api_url="http://${server_name}:${port}/dns/api/config/query"

whereis jq | grep /usr/bin/jq > /dev/null
if [ $? -eq 0 ]; then
    curl -s $api_url -X POST -d '{"ns_token":"'$ns_token'", "get_NS_config":"get_NS_config"}' | jq .
else
    curl -s $api_url -X POST -d '{"ns_token":"'$ns_token'", "get_NS_config":"get_NS_config"}'
fi
