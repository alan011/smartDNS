from django.db import models
from django.utils import timezone
from .dns_settings import ACL_NAME_DEFINE, RECORD_TYPE_CHOICES, TTL_CHOICES, ZONE_TYPE_CHOICES, CLUSTER_NAME_DEFINE

YES_OR_NO = ((0, '否'),(1, '是'))

class BindConfigACL(models.Model):
    id              = models.AutoField('ID', primary_key=True)
    subnet          = models.CharField('子网',max_length=64, null=True, blank=True, unique=True)
    acl_name        = models.CharField('子网分组', max_length=32, choices=ACL_NAME_DEFINE, default='devsubnet')
    # resolv_area     = models.CharField('解析区域', max_length=32, choices=RESOLV_AREA_CHOICES,default='internal')
    description     = models.CharField('描述',max_length=512, default='')
    add_time        = models.DateTimeField('添加时间',auto_now_add=True)
    is_applied      = models.IntegerField('是否已应用',choices=YES_OR_NO, default=0)
    is_deleted      = models.IntegerField('是否已删除',choices=YES_OR_NO, default=0)

    ### For multi-clusters deployment. Each cluster only get its own data distinguished by this field.
    cluster_name        = models.CharField('集群名称', choices=CLUSTER_NAME_DEFINE.items(), max_length=32, default='')

    def __str__(self):
        return self.subnet

class BindConfigView(models.Model):
    id              = models.AutoField('ID',primary_key=True)
    name            = models.CharField('view名称',max_length=64, null=True, blank=True, unique=True)
    readable_name   = models.CharField('别名',max_length=64, null=True, blank=True, unique=True)
    acl_name        = models.CharField('acl引用', max_length=32, choices=ACL_NAME_DEFINE, default='devsubnet')
    allowed_key     = models.CharField('key配置', max_length=16, default='dev-key')
    description     = models.CharField('描述',max_length=512, default='')
    add_time        = models.DateTimeField('添加时间',auto_now_add=True)
    is_applied      = models.IntegerField('是否已应用',choices=YES_OR_NO, default=0)
    is_deleted      = models.IntegerField('是否已删除',choices=YES_OR_NO, default=0)

    ### For multi-clusters deployment. Each cluster only get its own data distinguished by this field.
    cluster_name        = models.CharField('集群名称', choices=CLUSTER_NAME_DEFINE.items(), max_length=32, default='')

    def __str__(self):
        return self.name

class BindConfigZone(models.Model):
    id              = models.AutoField('ID',primary_key=True)
    name            = models.CharField('域名',max_length=64, null=True, blank=True, unique=True)
    zone_type       = models.CharField('域名类型', max_length=16, choices=ZONE_TYPE_CHOICES, default='inner_domain')
    description     = models.CharField('描述',max_length=512, default='')
    add_time        = models.DateTimeField('添加时间',auto_now_add=True)
    is_deleted      = models.IntegerField('是否已删除',choices=YES_OR_NO, default=0)
    # file_path       = models.CharField('zone文件路径',max_length=128, null=True, blank=True, unique=True)
    # view_belong     = models.ForeignKey(BindConfigView, on_delete=models.CASCADE, related_name="containing_zones")
    # is_fixed        = models.IntegerField('是否为固定zone文件',choices=YES_OR_NO, default=0)

    def __str__(self):
        return self.name

class BindNSRecord(models.Model):
    id              = models.AutoField('ID',primary_key=True)

    ### We cannot use 'ID' field to sync data across multi-clusters(means multi db). So we designed a 'UUID' field.
    uuid            = models.CharField('唯一标识',max_length=64, null=True, blank=True)
    # uuid            = models.CharField('唯一标识',max_length=64, unique=True)

    name            = models.CharField('解析名称',max_length=64, null=True, blank=True)
    record_type     = models.CharField('记录类型', max_length=32, choices=RECORD_TYPE_CHOICES, default='devsubnet')
    resolv_addr     = models.CharField('解析地址', max_length=64, default='')
    zone_belong     = models.ForeignKey(BindConfigZone, on_delete=models.CASCADE, related_name="containing_records")
    view_belong     = models.ForeignKey(BindConfigView, on_delete=models.CASCADE, related_name="containing_records", null=True, blank=True)
    ttl_seconds     = models.IntegerField("TTL设置", choices=TTL_CHOICES, default=600)
    description     = models.CharField('描述',max_length=512, default='')
    add_time        = models.DateTimeField('添加时间',auto_now_add=True)
    is_applied      = models.IntegerField('是否已应用',choices=YES_OR_NO, default=0)
    is_disabled     = models.IntegerField('是否已失效',choices=YES_OR_NO, default=0)
    is_deleted      = models.IntegerField('是否已删除',choices=YES_OR_NO, default=0)

    ### For multi-clusters deployment. Each cluster only get its own data distinguished by this field.
    cluster_name        = models.CharField('集群名称', choices=CLUSTER_NAME_DEFINE.items(), max_length=32, default='')

    def __str__(self):
        return self.name

class BindFileRegister(models.Model):
    FILE_TYPE_CHOICES = ((0,'zone file'),(1,'iplist config file'),(2, 'named.conf'))
    id              = models.AutoField('ID',primary_key=True)
    file_path       = models.CharField('文件路径',max_length=128, null=True, blank=True, unique=True)
    file_type       = models.IntegerField('文件类型',choices=FILE_TYPE_CHOICES, default=0)
    add_time        = models.DateTimeField('添加时间',auto_now_add=True)
    is_deleted      = models.IntegerField('是否已删除',choices=YES_OR_NO, default=0)


class MultiClustersDataSyncCache(models.Model):
    id              = models.AutoField('ID',primary_key=True)

    ### Time of syncing data by 'ns_api_cluster_agent.py'
    origin_synctime = models.DateTimeField('首次同步时间', default=timezone.now)

    ### The real data.
    data_content    = models.CharField('数据内容', max_length=512, default='')

    ### If failed in the origin data-syncing, the failed cluster name will be record in this field 'failed_cluster'.
    failed_cluster  = models.CharField('集群名称', choices=CLUSTER_NAME_DEFINE.items(), max_length=32, default='')
    sync_url        = models.CharField('请求域名', max_length=128, default='')

    ### If failed in the origin data-syncing, re-rsync program will retry every one minutes till upto 15 times.
    retry_count     = models.IntegerField('重新同步次数', default=0)
    is_synced       = models.IntegerField('是否已成功推送', choices=YES_OR_NO, default=0)
