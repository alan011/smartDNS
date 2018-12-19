from dns import dns_settings
class NSApiAuth(object):
    simple_auth_string = "nqEyAW8mOCALbs0YBN4FdVikWQlVMeRo"
    """
    By now, simply to check a firm string with length 32. Complicated auth method comes with later version.
    """
    def hostAllowedCheck(self, request):
        remote_addr = request.META['REMOTE_ADDR']
        # print("self.host_allowed_list: %s, remote_addr: %s" % (self.host_allowed_list,remote_addr))
        if remote_addr in self.host_allowed_list:
            return True
        else:
            return False

    def simpleAuthStringCheck(self, auth_string):
        if auth_string == self.simple_auth_string:
            return True
        else:
            return False

    def setHostAllowedList(self):
        self.host_allowed_list = dns_settings.WEB_UI_SERVER + ['127.0.0.1', dns_settings.MASTER_SERVER]

    def simpleAuth(self, auth_string, request):
        self.setHostAllowedList()
        host_allowed_check = self.hostAllowedCheck(request)
        simple_auth_string_check = self.simpleAuthStringCheck(auth_string)
        return (host_allowed_check and simple_auth_string_check)

class NSClusterAuth(NSApiAuth):
    this_is_master = dns_settings.THIS_IS_MASTER
    simple_auth_string = "ZKwj9gToQyzcQSrqtnTuuf4rZBW2dsGB"
    master_server  = dns_settings.MASTER_SERVER
    """
    Only used for slave server. To identify whether requests from master are legal or not.
    """
    pass

class NSMultiClusterAuth(NSApiAuth):
    """
    Used in 'ns_api_cluster_agent.py' for synchronizing data accross multi-clusters.
    """
    simple_auth_string = "rs6PzzmWgxUUxXklvk7spoxHGCLOFloJ"
    def setHostAllowedList(self):
        if getattr(dns_settings, 'ENABLE_MULTI_CLUSTERS') and getattr(dns_settings, 'MAIN_CLUSTER_MASTER') and getattr(dns_settings, 'OTHER_CLUSTER_MASTERS'):
            self.host_allowed_list = dns_settings.WEB_UI_SERVER + ['127.0.0.1', dns_settings.MASTER_SERVER, dns_settings.MAIN_CLUSTER_MASTER[1]] + [val for val in dns_settings.OTHER_CLUSTER_MASTERS.values()]
        else:
            super().setHostAllowedList()

class NSAuthForConfigQuery(NSApiAuth):
    simple_auth_string = "e01pdXVV7kaOykULCEGHNbv4DnMObrOO"
    """
    Config query API use this token to authenticate clients.
    """
    pass
