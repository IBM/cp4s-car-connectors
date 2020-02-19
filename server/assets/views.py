from .models import XRefProperty, Vulnerability, Asset, IPAddress, MACAddress, Host, App, Port
from rest_framework import viewsets, permissions
from assets import serializers


class XRefPropertyViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = XRefProperty.objects.all()
    serializer_class = serializers.XRefPropertySerializer


class VulnerabilityViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Vulnerability.objects.all()
    serializer_class = serializers.VulnerabilitySerializer


class AssetViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Asset.objects.all()
    serializer_class = serializers.AssetSerializer


class IPAddressViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = IPAddress.objects.all()
    serializer_class = serializers.IPAddressSerializer


class MACAddressViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = MACAddress.objects.all()
    serializer_class = serializers.MACAddressSerializer


class HostViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Host.objects.all()
    serializer_class = serializers.HostSerializer


class AppViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = App.objects.all()
    serializer_class = serializers.AppSerializer


class PortViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Port.objects.all()
    serializer_class = serializers.PortSerializer

