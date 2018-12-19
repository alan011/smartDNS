from django.http                  import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators      import method_decorator
from django.views.generic         import View

from .ns_api_auth     import NSClusterAuth
from .ns_api_common   import NSApiCommon
from dns.ns_factory.ns_config_handler import BindResolvHandler, BindACLConfigHandler, BindNamedConfHandler

import json, re, os


@method_decorator(csrf_exempt, name='dispatch')
class NSApiClusterNotice(View, NSApiCommon, NSClusterAuth):
    legal_fields = ['ns_token',          ### Type str: A 32-length-string
                    'notice_from_master' ### Type str: By now, options: 'APPLY_RESOLV', 'APPLY_ACL', 'APPLY_NAMED_CONF' is supported.
                   ]

    def post(self, request):
        if self.this_is_master:
            return HttpResponse('ERROR: this API is not for master server.', status=400)

        ### Simply check post field.
        post_data   = self.checkPostData(request, self.legal_fields)
        if isinstance(post_data, HttpResponse):   ### Means error occured.
            return post_data

        ### Authentication
        if not self.simpleAuth(post_data['ns_token'], request):
            return HttpResponse('ERROR: Authentication failed.', status=403)

        if post_data['notice_from_master'] == "APPLY_RESOLV":
            config_handler = BindResolvHandler()
            file_write_ret = config_handler.writeZoneFiles()
            if not isinstance(file_write_ret, dict):
                return HttpResponse(str(file_write_ret), status=400)
        elif post_data['notice_from_master'] == "APPLY_NAMED_CONF":
            config_handler = BindNamedConfHandler()
            file_write_ret = config_handler.configBindNamedConf()
            if not isinstance(file_write_ret, dict):
                return HttpResponse(str(file_write_ret), status=400)
        elif post_data['notice_from_master'] == "APPLY_ACL":
            config_handler = BindACLConfigHandler()
            file_write_ret = config_handler.configBindACL()
            if not isinstance(file_write_ret, dict):
                return HttpResponse(str(file_write_ret), status=400)
        else:
            return HttpResponse('ERROR: unsupported notice: %s' % post_data['notice_from_master'], status=400)

        return HttpResponse(json.dumps(file_write_ret), content_type='application/json')
