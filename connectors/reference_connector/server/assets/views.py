from django.db.models import Max

from .change_log import init_event_receivers
from .models import XRefProperty, Vulnerability, Asset, IPAddress, MACAddress, Host, App, Port, ChangeLog, Site
from rest_framework import viewsets, permissions
from assets import serializers
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound


class ModelViewSet_WithPkFiltering(viewsets.ModelViewSet):
    def get_queryset(self):
        qs = super().get_queryset()
        pk = self.request.query_params.get('pk')
        if pk:
            return qs.filter(pk__in=pk.split(','))
        return qs


class XRefPropertyViewSet(ModelViewSet_WithPkFiltering):
    permission_classes = [permissions.IsAuthenticated]
    queryset = XRefProperty.objects.all()
    serializer_class = serializers.XRefPropertySerializer


class VulnerabilityViewSet(ModelViewSet_WithPkFiltering):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Vulnerability.objects.all()
    serializer_class = serializers.VulnerabilitySerializer


class SiteViewSet(ModelViewSet_WithPkFiltering):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Site.objects.all()
    serializer_class = serializers.SiteSerializer


class AssetViewSet(ModelViewSet_WithPkFiltering):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Asset.objects.all()
    serializer_class = serializers.AssetSerializer


class IPAddressViewSet(ModelViewSet_WithPkFiltering):
    permission_classes = [permissions.IsAuthenticated]
    queryset = IPAddress.objects.all()
    serializer_class = serializers.IPAddressSerializer


class MACAddressViewSet(ModelViewSet_WithPkFiltering):
    permission_classes = [permissions.IsAuthenticated]
    queryset = MACAddress.objects.all()
    serializer_class = serializers.MACAddressSerializer


class HostViewSet(ModelViewSet_WithPkFiltering):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Host.objects.all()
    serializer_class = serializers.HostSerializer


class AppViewSet(ModelViewSet_WithPkFiltering):
    permission_classes = [permissions.IsAuthenticated]
    queryset = App.objects.all()
    serializer_class = serializers.AppSerializer


class PortViewSet(ModelViewSet_WithPkFiltering):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Port.objects.all()
    serializer_class = serializers.PortSerializer

def model_state_id(request):
    sp = ChangeLog.objects.aggregate(Max('pk'))['pk__max']
    return JsonResponse({'model_state_id' : str(sp)})

model_to_endpoint_map = {'App': 'apps', 'Asset': 'assets', 'Host': 'hosts', 'IPAddress': 'ip_addresses', 'MACAddress': 'mac_addresses', 'Port': '', 'Vulnerability': 'vulnerabilities', 'Port': 'ports', 'XRefProperty': 'xrefproperties', 'Site': 'sites'}

def delta(request):
    _from = request.GET.get('from')
    if not _from: return HttpResponseBadRequest()
    _from = int(_from)

    _to = request.GET.get('to')
    if not _to: return HttpResponseBadRequest()
    _to = int(_to)

    if _from == _to: return JsonResponse({})
    if _from > _to: return HttpResponseBadRequest()

    _from += 1
    res = ChangeLog.objects.filter(pk__gte=_from, pk__lte=_to)
    if len(res) < (_to - _from): return HttpResponseNotFound

    delta = {}
    for cl in res:
        data = delta.get(model_to_endpoint_map[cl.model])
        if not data:
            data = {'updates':set(), 'deletions':set()}
            delta[model_to_endpoint_map[cl.model]] = data
        if cl.deleted: data['deletions'].add(cl.uid)
        else: data['updates'].add(cl.uid)

    res = {}
    for key in delta:
        value = delta[key]
        res[key] = {'updates':list(value['updates']), 'deletions':list(value['deletions'])}

    return JsonResponse({'delta' : res})

init_event_receivers()
