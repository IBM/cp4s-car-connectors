from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from assets import views


router = routers.DefaultRouter()
router.register('xrefproperties', views.XRefPropertyViewSet)
router.register('vulnerabilities', views.VulnerabilityViewSet)
router.register('assets', views.AssetViewSet)
router.register('ip_addresses', views.IPAddressViewSet)
router.register('mac_addresses', views.MACAddressViewSet)
router.register('hosts', views.HostViewSet)
router.register('ports', views.PortViewSet)
router.register('apps', views.AppViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

