FROM python:3.6-alpine
LABEL maintainer="Fabio Todaro <ft@ovalmoney.com>"

ARG BUILD_DATE
ARG DOCKER_REPO
ARG VERSION
ARG VCS_REF

LABEL org.label-schema.schema-version="1.0" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name=$DOCKER_REPO \
      org.label-schema.version=$VERSION \
      org.label-schema.description="Prometheus metrics exporter for Celery" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/OvalMoney/celery-exporter"

WORKDIR /app/

COPY requirements/ ./requirements

RUN pip install -r ./requirements/requirements.txt

COPY setup.py README.md ./
COPY celery_exporter/  ./celery_exporter/
RUN pip install --no-deps -e .

ENTRYPOINT ["celery-exporter"]
CMD []

EXPOSE 9540
