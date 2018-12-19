from django.conf import settings

PROJECT_BASE_DIR = settings.BASE_DIR + '/..'

API_PORT='10081'

##########################
#### cluster config  #####
##########################

### To config this server as master server or slave server.
### All API except 'cluster api' will be disabled if this server is not a master.
### Master will notice other servers to apply bind config files according to DB, if any changes needs to be applied.
### Slave servers will apply bind config according to DB in this cluster, when receive notice from master.
### ALL the three of bellow VARs should be defined. If no slave server, "SLAVE_SERVER_LIST" should be an empty list.
THIS_IS_MASTER    = True
MASTER_SERVER     = "172.16.35.177"
SLAVE_SERVER_LIST = ["172.16.35.178"]

##########################
## Multi-cluster config  #
##########################

### This means that you have multiple master-slaves clusters.
### Most use case is that: you have more than one IDC, and you want to setup one master-slaves-cluster in each IDC, with all data  auto-synchronized across these IDCs.

### Set 'ENABLE_MULTI_CLUSTERS' to True to enable this feature. If you don't need this feature, set it to False.
ENABLE_MULTI_CLUSTERS      = False

### Cluster name defination used in models.py. If ENABLE_MULTI_CLUSTERS is True, this dict should not be empty.
CLUSTER_NAME_DEFINE      = {'ALL':'所有集群',
                            'cluster1':'测试集群1',
                            'cluster2': '测试集群2',
                           }

### To tell myself who I am.
THIS_CLUSTER_NAME        = 'cluster1'

### User make changes on this 'MAIN_CLUSTER_MASTER', and other cluster masters are always waiting notice from this master.
### It's a tuple with two elements, first one is main cluster name, second if main cluster's master IP.
### Its name should be one of 'CLUSTER_NAME_DEFINE'.
MAIN_CLUSTER_MASTER      = ('cluster1', '172.16.35.177')

### A dict to record other cluster's name and its master IP. All names should be in 'CLUSTER_NAME_DEFINE'.
OTHER_CLUSTER_MASTERS    = {'cluster2': '172.16.40.143',
                           }

##########################
###### Basic config ######
##########################

BIND_ACL_CONFIG_TEMPLATE_FILE   = PROJECT_BASE_DIR + '/file_templates/iplist.config.temp'
# BIND_ACL_CONFIG_TARGET_FILE_DIR = '/etc/named/'
BIND_ACL_CONFIG_TARGET_FILE     = '/etc/named/iplist.cfg'
BIND_MAIN_CONFIG_TEMPLATE_FILE  = PROJECT_BASE_DIR + '/file_templates/named.conf.temp'
BIND_MAIN_CONFIG_TARGET_FILE    = '/etc/named.conf'
BIND_ZONE_FILE_ROOT             = '/var/named/named.zones/'
BIND_RESOLV_TEMPLATE_FILE       = PROJECT_BASE_DIR + '/file_templates/zone_name.view_name.zone.temp'


##########################
### choices for models ###
##########################

ACL_NAME_DEFINE         = (
                           ('default','全网络解析'),
                           ('basic','OP基础环境网络'),
                           ('citest','citest稳定区环境网络'),
                           ('citestexp','citest体验区环境网络'),
                           ('dev',"dev环境网络"),
                           ('gld',"gld环境网络"),
                           ('gldexp',"gldexp环境网络"),
                           ('cibigdata',"大数据测试环境网络"),
                           ('loadtest','loadtest压测环境'),
                          )

RECORD_TYPE_CHOICES     = (('A',    'A记录'),
                           ('AAAA', '4A记录'),
                           ('CNAME','CNAME'),
                           ('MX',   'MX记录'),
                          )

VIEW_KEY_DEFINE         = {'basic-key':  'O0ghR0jngDMiY05MG3JdGg==',
                           'citest-key':  'Yyc29YkRtokXHlAgo4zgvA==',
                           'citestexp-key':  '3mHJohnRkdZTj/dxDqtRDA==',
                           'dev-key':'2MxcQUwLhy23IGWUbjJaig==',
                           'gld-key':'9rbBgcJsthP77sePMkWjtA==',
                           'gldexp-key':'esKLBPF0krabvilxCVZUtw==',
                           'vpcprod-key':'wli370J5SsfHTVALB1/ajw==',
                           'vpcprodexp-key':'x+mzJojf2M4sy5Hzp/XiPg==',
                           'cibigdata-key':  'Yyc29YkRtokXHlAgo4zgvA==',
                           'loadtest-key':   '8JSd6Cqt4lw0PvlKjNoF5g==',
                           'default-key':   'uGfTJydW6MHkPJsHiVekjQ==',
                           }

TTL_CHOICES             = ( (600, '10 min'),
                            (3600, '1 hour'),
                            (86400, '1 day'),
                          )
ZONE_TYPE_CHOICES       = (('inner_domain','内网域名'),
                          #  ('outer_domain','公网域名'),
                        )
##########################
### api authentication ###
##########################


### WEB-UI server should have READ and WRITE permission with all dns objects.
WEB_UI_SERVER = ['127.0.0.1']


##########################
#### resolv settings #####
##########################

NS_SERVERS = ("ns1.shishike.com",
             "ns2.shishike.com",
            )


##########################
## bind service settings #
##########################

SERVICE_SCRIPT = "/etc/init.d/named"
SERVICE_RELOAD =True   ### Use 'service named reload' by default. If set to False, it will use 'service named restart'.
