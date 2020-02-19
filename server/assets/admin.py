from django.contrib import admin

from .models import XRefProperty, Vulnerability, Asset, IPAddress, MACAddress, Host, App, Port, AssetModelSize

class VulnInline(admin.TabularInline):
    model = Asset.vulnerabilities.through

class AppInline(admin.TabularInline):
    model = App.assets.through

class AssetAdmin(admin.ModelAdmin):
    model = Asset
    inlines = [
        VulnInline,
        AppInline,
    ]
    exclude = ('vulnerabilities',)

class IPInline(admin.TabularInline):
    model = MACAddress.ip_addresses.through

class MACAddressAdmin(admin.ModelAdmin):
    model = MACAddress
    inlines = [
        IPInline,
    ]
    exclude = ('ip_addresses',)

class PortAppInline(admin.TabularInline):
    model = Port.apps.through

class PortIpInline(admin.TabularInline):
    model = Port.ip_addresses.through

class PortAdmin(admin.ModelAdmin):
    model = Port
    inlines = [
        PortAppInline,
        PortIpInline,
    ]
    exclude = ('apps', 'ip_addresses')

admin.site.register(XRefProperty)
admin.site.register(Vulnerability)
admin.site.register(Asset, AssetAdmin)
admin.site.register(IPAddress)
admin.site.register(MACAddress, MACAddressAdmin)
admin.site.register(Host)
admin.site.register(App)
admin.site.register(Port, PortAdmin)
admin.site.register(AssetModelSize)
