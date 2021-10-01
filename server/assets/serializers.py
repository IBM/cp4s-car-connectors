from .models import XRefProperty, Vulnerability, Asset, IPAddress, MACAddress, Host, App, Port, Site
from rest_framework import serializers


class XRefPropertySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = XRefProperty
        fields = ['pk', 'extref_typename', 'extref_value', 'q_extref_typeid']


class VulnerabilitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Vulnerability
        fields = ['pk', 'name', 'published_on', 'disclosed_on', 'updated_on', 'vcvssbmid', 'base_score', 'xref_properties']


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Site
        fields = ['pk', 'name', 'address']


class AssetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Asset
        fields = ['pk', 'name', 'type', 'initial_value', 'site', 'vulnerabilities']


class IPAddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = IPAddress
        fields = ['pk', 'address', 'asset']


class MACAddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MACAddress
        fields = ['pk', 'address', 'asset', 'ip_addresses']


class HostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Host
        fields = ['pk', 'host', 'asset']


class AppSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = App
        fields = ['pk', 'name', 'assets']


class PortSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Port
        fields = ['pk', 'port_number', 'layer7application', 'protocol', 'apps', 'ip_addresses']

