from django.contrib import admin
from .models import BindConfigACL, BindConfigView, BindNSRecord, BindConfigZone, BindFileRegister

# Register your models here.
class BindConfigACLAdmin(admin.ModelAdmin):
    list_display       = ('id','subnet','acl_name','add_time','is_applied','is_deleted','description')
    list_display_links = ('id','subnet')
    search_fields      = ('subnet','description')
    ordering           = ('id','add_time')
    list_per_page      = 50

class BindConfigViewAdmin(admin.ModelAdmin):
    list_display       = ('id','name','acl_name','allowed_key','add_time','is_applied','is_deleted','description')
    list_display_links = ('id','name')
    search_fields      = ('name','description')
    ordering           = ('id','add_time')
    list_per_page      = 50

class BindConfigZoneAdmin(admin.ModelAdmin):
    list_display       = ('id','name','zone_type','add_time','is_deleted','description')
    list_display_links = ('id','name')
    search_fields      = ('name','description')
    ordering           = ('id','add_time')
    list_per_page      = 50

class BindNSRecordAdmin(admin.ModelAdmin):
    list_display       = ('id','name','record_type','resolv_addr','ttl_seconds','zone_belong','view_belong','add_time','is_disabled','is_applied','is_deleted','description')
    list_display_links = ('id','name')
    search_fields      = ('name','description','resolv_addr')
    ordering           = ('id','add_time')
    list_per_page      = 50

class BindFileRegisterAdmin(admin.ModelAdmin):
    list_display       = ('id','file_path','file_type','is_deleted',)
    list_display_links = ('id','file_path')
    search_fields      = ('file_path',)
    ordering           = ('id',)
    list_per_page      = 50

admin.site.register(BindConfigACL,BindConfigACLAdmin)
admin.site.register(BindConfigView,BindConfigViewAdmin)
admin.site.register(BindConfigZone,BindConfigZoneAdmin)
admin.site.register(BindNSRecord,BindNSRecordAdmin)
admin.site.register(BindFileRegister,BindFileRegisterAdmin)
