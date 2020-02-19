from django.db import models

class XRefProperty(models.Model):
    extref_typename = models.CharField(max_length=80)
    extref_value = models.CharField(max_length=80)
    q_extref_typeid = models.IntegerField(default=0)
    def __str__(self):
        return self.extref_typename
    class Meta:
        verbose_name = "XRef Property"
        verbose_name_plural = "XRef Properties"


class Vulnerability(models.Model):
    name = models.CharField(max_length=80)
    published_on = models.IntegerField(default=1342915876000)
    disclosed_on = models.IntegerField(default=1342915876000)
    updated_on = models.IntegerField(default=1342915876000)
    vcvssbmid = models.IntegerField(default=71885)
    base_score = models.FloatField(default=7.5)
    xref_properties = models.ManyToManyField(XRefProperty, blank=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Vulnerability"
        verbose_name_plural = "Vulnerabilities"


class Asset(models.Model):
    name = models.CharField(max_length=80)
    type = models.CharField(max_length=80, default='Other')
    vulnerabilities = models.ManyToManyField(Vulnerability, blank=True)
    def __str__(self):
        return self.name


class IPAddress(models.Model):
    address = models.CharField(max_length=20)
    asset = models.ForeignKey(Asset, related_name='ip_addresses', on_delete=models.CASCADE)
    def __str__(self):
        return self.address
    class Meta:
        verbose_name = "IP Address"
        verbose_name_plural = "IP Addresses"


class MACAddress(models.Model):
    address = models.CharField(max_length=30)
    asset = models.ForeignKey(Asset, related_name='mac_addresses', on_delete=models.CASCADE)
    ip_addresses = models.ManyToManyField(IPAddress, blank=True)
    def __str__(self):
        return self.address
    class Meta:
        verbose_name = "MAC Address"
        verbose_name_plural = "MAC Addresses"


class Host(models.Model):
    host = models.CharField(max_length=80)
    asset = models.ForeignKey(Asset, related_name='host_names', on_delete=models.CASCADE)
    def __str__(self):
        return self.host


class App(models.Model):
    name = models.CharField(max_length=80)
    assets = models.ManyToManyField(Asset, blank=True)
    def __str__(self):
        return self.name


class Port(models.Model):
    port_number = models.IntegerField(default=8080)
    layer7application = models.CharField(max_length=80, default='UnknownApplication')
    protocol = models.CharField(max_length=80, default='tcp')
    apps = models.ManyToManyField(App, blank=True)
    ip_addresses = models.ManyToManyField(IPAddress, blank=True)
    def __str__(self):
        return str(self.port_number)


class AssetModelSize(models.Model):
    size = models.IntegerField(default=100)
    def __str__(self):
        return str(self.size)
    def save(self, *args, **kwargs):
        super(AssetModelSize, self).save(*args, **kwargs)
        from assets.populate import populate
        populate(self.size)
    class Meta:
        verbose_name_plural = "Asset Model Size"
