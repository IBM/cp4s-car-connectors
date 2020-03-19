from django.contrib import admin

from .models import XRefProperty, Vulnerability, Asset, IPAddress, MACAddress, Host, App, Port, AssetModelSize, ChangeLog

admin.site.register(XRefProperty)
admin.site.register(Vulnerability)
admin.site.register(Asset)
admin.site.register(IPAddress)
admin.site.register(MACAddress)
admin.site.register(Host)
admin.site.register(App)
admin.site.register(Port)
admin.site.register(AssetModelSize)
admin.site.register(ChangeLog)
