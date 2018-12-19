from django.conf.urls import url

from dns.ns_api import (
    NSApiACLAdd,    NSApiACLDelete,    NSApiACLModify,    NSApiACLQuery,    NSApiACLApply,
    NSApiZoneAdd,   NSApiZoneDelete,   NSApiZoneModify,   NSApiZoneQuery,
    NSApiViewAdd,   NSApiViewDelete,   NSApiViewModify,   NSApiViewQuery,   NSApiViewApply,
    NSApiResolvAdd, NSApiResolvDelete, NSApiResolvModify, NSApiResolvQuery, NSApiResolvApply,
    NSApiClusterNotice, serviceCheck,  NSApiClusterAgent, NSApiConfigQuery
)

app_name = 'dns'
urlpatterns = [
            url(r'^api/acl/add$',    NSApiACLAdd.as_view(),    name='NSApiACLAdd'),
            url(r'^api/acl/delete$', NSApiACLDelete.as_view(), name='NSApiACLDelete'),
            url(r'^api/acl/modify$', NSApiACLModify.as_view(), name='NSApiACLModify'),
            url(r'^api/acl/query$',  NSApiACLQuery.as_view(),  name='NSApiACLQuery'),
            url(r'^api/acl/apply$',  NSApiACLApply.as_view(),  name='NSApiACLApply'),
            url(r'^api/zone/add$',   NSApiZoneAdd.as_view(),   name='NSApiZoneAdd'),
            url(r'^api/zone/delete$',NSApiZoneDelete.as_view(),name='NSApiZoneDelete'),
            url(r'^api/zone/modify$',NSApiZoneModify.as_view(),name='NSApiZoneModify'),
            url(r'^api/zone/query$', NSApiZoneQuery.as_view(), name='NSApiZoneQuery'),
            url(r'^api/view/add$',   NSApiViewAdd.as_view(),   name='NSApiViewAdd'),
            url(r'^api/view/delete$',NSApiViewDelete.as_view(),name='NSApiViewDelete'),
            url(r'^api/view/modify$',NSApiViewModify.as_view(),name='NSApiViewModify'),
            url(r'^api/view/query$', NSApiViewQuery.as_view(), name='NSApiViewQuery'),
            url(r'^api/view/apply$', NSApiViewApply.as_view(), name='NSApiViewApply'),
            url(r'^api/resolv/add$',   NSApiResolvAdd.as_view(),   name='NSApiResolvAdd'),
            url(r'^api/resolv/delete$',NSApiResolvDelete.as_view(),name='NSApiResolvDelete'),
            url(r'^api/resolv/modify$',NSApiResolvModify.as_view(),name='NSApiResolvModify'),
            url(r'^api/resolv/query$', NSApiResolvQuery.as_view(), name='NSApiResolvQuery'),
            url(r'^api/resolv/apply$', NSApiResolvApply.as_view(), name='NSApiResolvApply'),
            url(r'^api/cluster/notice$', NSApiClusterNotice.as_view(), name='NSApiClusterNotice'),
            url(r'^api/service/check$', serviceCheck, name='NSApiServiceCheck'),
            url(r'^api/agent', NSApiClusterAgent.as_view(), name='NSApiClusterAgent'),
            url(r'^api/config/query', NSApiConfigQuery.as_view(), name='NSApiConfigQuery'),
              ]
