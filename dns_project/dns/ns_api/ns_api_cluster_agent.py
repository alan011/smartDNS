from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic         import View
from .ns_api_common import NSApiCommon, APICaller
from .ns_api_auth   import NSApiAuth, NSMultiClusterAuth
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators      import method_decorator
from dns import dns_settings
from django.utils import timezone
from dns.models import MultiClustersDataSyncCache
import json

@method_decorator(csrf_exempt, name='dispatch')
class NSApiClusterAgent(NSApiCommon, APICaller, NSMultiClusterAuth, View):
    action_support = ('add', 'delete', 'modify', 'query', 'apply','get_cache')
    action_for_data_sync = ('add', 'delete', 'modify')
    object_support = ('iplist', 'view', 'zone', 'resolv','cache')

    def post(self, request, *args, **kwargs):
        ### To parse json data.
        post_data = self.checkPostData(request, field_require=False)
        if isinstance(post_data, HttpResponse):   ### Means error occured.
            return post_data

        ### To anthenticate.
        if not self.simpleAuth(post_data['ns_token'], request):
            return HttpResponse('ERROR: Authentication failed!\n', status=403)

        ### to check key field.
        if post_data.get('action') not in self.action_support or post_data.get('object') not in self.object_support:
            return HttpResponse('ERROR: Illegal request.\n', stutus=400)
        action   = post_data.pop('action')
        obj_type = post_data.pop('object')

        ### to dispatch next post request.
        if obj_type == 'iplist':
            if action == 'add':
                next_url = reverse('dns:NSApiACLAdd')
            elif action == 'delete':
                next_url = reverse('dns:NSApiACLDelete')
            elif action == 'modify':
                next_url = reverse('dns:NSApiACLModify')
            elif action == 'query':
                next_url = reverse('dns:NSApiACLQuery')
            elif action == 'apply':
                next_url = reverse('dns:NSApiACLApply')
        elif obj_type == 'view':
            if action == 'add':
                next_url = reverse('dns:NSApiViewAdd')
            elif action == 'delete':
                next_url = reverse('dns:NSApiViewDelete')
            elif action == 'modify':
                next_url = reverse('dns:NSApiViewModify')
            elif action == 'query':
                next_url = reverse('dns:NSApiViewQuery')
            elif action == 'apply':
                next_url = reverse('dns:NSApiViewApply')
        elif obj_type == 'zone':
            if action == 'add':
                next_url = reverse('dns:NSApiZoneAdd')
            elif action == 'delete':
                next_url = reverse('dns:NSApiZoneDelete')
            elif action == 'modify':
                next_url = reverse('dns:NSApiZoneModify')
            elif action == 'query':
                next_url = reverse('dns:NSApiZoneQuery')
        elif obj_type == 'resolv':
            if action == 'add':
                next_url = reverse('dns:NSApiResolvAdd')
                if 'resolv_uuid' not in post_data:
                    post_data['resolv_uuid'] =self.genUUID(64)
            elif action == 'delete':
                next_url = reverse('dns:NSApiResolvDelete')
            elif action == 'modify':
                next_url = reverse('dns:NSApiResolvModify')
            elif action == 'query':
                next_url = reverse('dns:NSApiResolvQuery')
            elif action == 'apply':
                next_url = reverse('dns:NSApiResolvApply')
        elif obj_type == 'cache' and action == 'get_cache':
            queryset = MultiClustersDataSyncCache.objects.filter(is_synced=0, retry_count=15)
            failed_clusters = {}
            for obj in queryset:
                if obj.failed_cluster in failed_clusters:
                    failed_clusters[obj.failed_cluster]['count'] += 1
                else:
                    failed_clusters[obj.failed_cluster] = {'alias_name':dns_settings.CLUSTER_NAME_DEFINE.get(obj.failed_cluster),
                                                           'count':1,
                                                          }

            ret_data = {'result':'SUCCESS',
                        'failed_clusters':failed_clusters,
                        }

            return HttpResponse(json.dumps(ret_data),content_type='application/json')

        ### To call inner APIs.
        post_data['ns_token'] = NSApiAuth.simple_auth_string
        print(post_data)
        action_result = self.post_caller('http://127.0.0.1:%s%s' % (dns_settings.API_PORT,next_url), post_data)
        if not isinstance(action_result, dict):
            action_result = {'result':'FAILED','message':action_result}

        ### To synchronize data to other clusters.
        if dns_settings.ENABLE_MULTI_CLUSTERS and dns_settings.OTHER_CLUSTER_MASTERS and action in self.action_for_data_sync and dns_settings.THIS_CLUSTER_NAME == dns_settings.MAIN_CLUSTER_MASTER[0]:
            post_data['ns_token'] = self.simple_auth_string
            post_data['action']   = action
            post_data['object']   = obj_type
            next_url = reverse('dns:NSApiClusterAgent')
            action_result['message'] = 'Main Cluster: %s; ' % action_result['message']
            for cluster_name,master_ip in dns_settings.OTHER_CLUSTER_MASTERS.items():
                sync_url = 'http://%s%s' % (master_ip, next_url)
                tmp_result = self.post_caller(sync_url, post_data)
                time_now = timezone.now()
                failed_tag = 0
                if isinstance(tmp_result, dict):
                    if tmp_result['result'] != 'SUCCESS':
                        action_result['result'] = tmp_result['result']
                        failed_tag += 1
                    action_result['message'] += 'Cluster %s: %s; ' % (cluster_name, tmp_result['message'])
                else:
                    action_result['result'] = 'FAILED'
                    action_result['message'] += 'Cluster %s: %s; ' % (cluster_name, str(tmp_result))
                    failed_tag += 1

                if failed_tag:
                    sync_cache_obj_attr = {'origin_synctime':time_now,
                                           'data_content':json.dumps(post_data),
                                           'sync_url':sync_url,
                                           'failed_cluster':cluster_name,
                                           }
                    sync_cache_obj = MultiClustersDataSyncCache(**sync_cache_obj_attr)
                    sync_cache_obj.save()

        return HttpResponse(json.dumps(action_result), content_type='application/json')
