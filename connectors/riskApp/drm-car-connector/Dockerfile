FROM registry.access.redhat.com/ubi8/python-36

USER root
RUN yum update-minimal --security --sec-severity=Important --sec-severity=Critical --disableplugin=subscription-manager -y && rm -rf /var/cache/yum
RUN yum update libnghttp2 kernel-headers gnutls git systemd-libs systemd-pam systemd --disableplugin=subscription-manager -y && rm -rf /var/cache/yum
RUN yum -y remove nodejs && rm -rf /var/cache/yum
USER 1001

COPY . /usr/src/app
# Licence needs to added when we get it for 1.4 release
# COPY /licenses/LA_en /licenses/LA_en

WORKDIR /usr/src/app

LABEL name="drm-car-connector" \
	vendor="IBM" \
	summary="DATA RISK Management connector for CP4S CAR service." \
	release="1.5" \
	version="1.5.0.0" \
	description="DATA RISK Management for CP4S CAR service."

RUN pip install -r requirements.txt

CMD python3 -tenantUrl=${TENANT_URL} -username=${USERNAME} -password=${PASSWORD} -pageSize=${PAGE_SIZE} -car-service-url=${CAR_SERVICE_URL} -car-service-key=${CAR_SERVICE_KEY} -car-service-password=${CAR_SERVICE_PASSWORD} -source=${SOURCE}