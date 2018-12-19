from django.http                  import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators      import method_decorator
from django.views.generic         import View
from .ns_api_common import NSApiCommon
from .ns_api_auth   import NSAuthForConfigQuery
from dns import dns_settings
import re, json

@method_decorator(csrf_exempt, name='dispatch')
class NSApiConfigQuery(NSApiCommon, NSAuthForConfigQuery, View):
    """
    To return NS API config dict.
    """

    def post(self, request, *args, **kwargs):
        ### To parse json data.
        post_data = self.checkPostData(request, field_require=False)
        if isinstance(post_data, HttpResponse):   ### Means error occured.
            return post_data

        ### To anthenticate.
        if not self.simpleAuth(post_data['ns_token'], request):
            return HttpResponse('ERROR: Authentication failed!\n', status=403)

        if post_data.get('get_NS_config') != 'get_NS_config':
            return HttpResponse('ERROR: Illegal request.\n', stutus=400)

        ret_data = {}
        for attr in dir(dns_settings):
            if not re.search('^__', attr) and attr != 'settings':
                ret_data[attr] = getattr(dns_settings,attr)
        return HttpResponse(json.dumps(ret_data), content_type='application/json')
