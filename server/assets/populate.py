import socket, struct
from .models import XRefProperty, Vulnerability, Asset, IPAddress, MACAddress, Host, App, Port

NUMBER_OF_ASSETS = 10
assets = None

def create_XRefProps():
    print('generating XREF props')
    for i in range(3):
        prop = XRefProperty()
        prop.extref_typename = 'xref prop %d' % i
        prop.extref_value = 1000 + i
        prop.q_extref_typeid = 20 + i
        prop.save()

def create_vulns():
    print('generating vulns')
    for i in range(NUMBER_OF_ASSETS * 2):
        v = Vulnerability()
        v.name = 'Vulnerability %d' % i
        v.save()
        for xref in XRefProperty.objects.all()[:3]:
            v.xref_properties.add(xref)

def create_assets():
    print('generating assets')
    vulns = Vulnerability.objects.all()
    for i in range(NUMBER_OF_ASSETS):
        asset = Asset()
        asset.name = 'asset%d.domain.com' % i
        asset.save()
        asset.vulnerabilities.add(vulns[i * 2])
        asset.vulnerabilities.add(vulns[i * 2 + 1])

def create_ip_addresses():
    print('generating IP addresses')
    ip_int = 168430090
    for i in range(NUMBER_OF_ASSETS):
        ip_int += 1
        ip = IPAddress()
        ip.address = socket.inet_ntoa(struct.pack('!L', ip_int))
        ip.asset = assets[i]
        ip.save()

def create_mac_addresses():
    print('generating MAC addresses')
    mac_int = int('00:50:56:A6:E2:1D'.replace(':', ''), 16)
    for i in range(NUMBER_OF_ASSETS):
        mac_int += 1
        mac_hex = "{:012x}".format(mac_int)
        mac = MACAddress()
        mac.address = mac_str = ":".join(mac_hex[i:i+2] for i in range(0, len(mac_hex), 2))
        mac.asset = assets[i]
        mac.save()
        for ip in mac.asset.ip_addresses.all():
            mac.ip_addresses.add(ip); break

def create_hosts():
    print('generating hosts')
    for i in range(NUMBER_OF_ASSETS):
        host = Host()
        host.asset = assets[i]
        host.host = 'system%d.domain.com' % i
        host.save()

def create_apps():
    print('generating apps')
    for i in range(NUMBER_OF_ASSETS * 3):
        app = App()
        app.name = "Application %d" % i
        app.save()
        app.assets.add(assets[i // 3])

def create_ports():
    print('generating ports')
    port = Port();
    port.port_number = 8090;
    port.save();
    for app in App.objects.all():
        port.apps.add(app)
    for ip in IPAddress.objects.all():
        port.ip_addresses.add(ip)


def reset_db():
    XRefProperty.objects.all().delete()
    Vulnerability.objects.all().delete()
    Asset.objects.all().delete()
    IPAddress.objects.all().delete()
    MACAddress.objects.all().delete()
    Host.objects.all().delete()
    App.objects.all().delete()
    Port.objects.all().delete()

def populate(size):
    global NUMBER_OF_ASSETS, assets
    NUMBER_OF_ASSETS = size
    reset_db()
    print('Populating db...')
    create_XRefProps()
    create_vulns()
    create_assets()
    assets = Asset.objects.all()
    create_ip_addresses()
    create_mac_addresses()
    create_hosts()
    create_apps()
    create_ports()
