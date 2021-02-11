FROM registry.access.redhat.com/ubi8/ubi-minimal as base
USER root
RUN  microdnf update -y && \
     microdnf install --nodocs python3 unzip openssl && \
     microdnf clean all && \
     rm -rf /var/cache/yum

FROM base as builder
USER root
RUN  microdnf install python3-pip
COPY requirements.txt requirements.txt
RUN  pip3 install -r requirements.txt --no-cache-dir 

FROM base
ARG TMP_USER_ID=1001
ARG TMP_USER_GROUP=1001

USER root

COPY . /usr/src/app

RUN chown -R ${TMP_USER_ID}:${TMP_USER_GROUP} /usr/src/app 

COPY --from=builder /usr/local/lib64/python3.6/site-packages /usr/local/lib64/python3.6/site-packages
COPY --from=builder /usr/local/lib/python3.6/site-packages /usr/local/lib/python3.6/site-packages
COPY --from=builder /usr/lib64/python3.6/site-packages /usr/lib64/python3.6/site-packages
COPY --from=builder /usr/lib/python3.6/site-packages /usr/lib/python3.6/site-packages

USER ${TMP_USER_ID}
COPY /licenses/LA_en /licenses/LA_en

WORKDIR /usr/src/app

LABEL name="<connector_name>-isc-car-connector" \
	vendor="IBM" \
	summary="<connector_summary>" \
	release="1.5" \
	version="<cp4s_version>" \
	description="<connector_description>"

CMD python3 app.py -server=${CONFIGURATION_AUTH_SERVER} -username=${CONFIGURATION_AUTH_USERNAME} -password=${CONFIGURATION_AUTH_PASSWORD} -api_key=${CONFIGURATION_AUTH_API_KEY} -car-service-url=${CAR_SERVICE_URL} -car-service-key=${CAR_SERVICE_KEY} -car-service-password=${CAR_SERVICE_PASSWORD} -car-service-url-for-token=${CAR_SERVICE_URL_FOR_AUTHTOKEN} -car-service-token=${CAR_SERVICE_AUTHTOKEN} -source=${CONNECTION_NAME}