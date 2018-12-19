import os
from dns.dns_settings import SERVICE_SCRIPT

class ServiceManager(object):
    service_script   = SERVICE_SCRIPT
    legal_operations = ('start','stop','reload','restart','status')

    def serviceOperate(self, operation):
        if operation in self.legal_operations:
            ret_code = os.system('%s %s' % (self.service_script, operation))
            if ret_code == 0:
                return 'SUCCESS'
            else:
                return 'ERROR: To %s named service failed, please check logs on server.' % operation
        else:
            return "ERROR: illegal operation: %s. " % operation
