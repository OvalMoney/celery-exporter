FROM python:3.6-alpine as base-image

ENV LANG=C.UTF-8

RUN ALPINE_GLIBC_BASE_URL="https://github.com/sgerrand/alpine-pkg-glibc/releases/download" && \
    ALPINE_GLIBC_PACKAGE_VERSION="2.29-r0" && \
    ALPINE_GLIBC_BASE_PACKAGE_FILENAME="glibc-$ALPINE_GLIBC_PACKAGE_VERSION.apk" && \
    ALPINE_GLIBC_BIN_PACKAGE_FILENAME="glibc-bin-$ALPINE_GLIBC_PACKAGE_VERSION.apk" && \
    ALPINE_GLIBC_I18N_PACKAGE_FILENAME="glibc-i18n-$ALPINE_GLIBC_PACKAGE_VERSION.apk" && \
    apk add --no-cache wget ca-certificates && \
    wget "https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub" -O /etc/apk/keys/sgerrand.rsa.pub && \
    wget "$ALPINE_GLIBC_BASE_URL/$ALPINE_GLIBC_PACKAGE_VERSION/$ALPINE_GLIBC_BASE_PACKAGE_FILENAME"  && \
    wget "$ALPINE_GLIBC_BASE_URL/$ALPINE_GLIBC_PACKAGE_VERSION/$ALPINE_GLIBC_BIN_PACKAGE_FILENAME"  && \
    wget "$ALPINE_GLIBC_BASE_URL/$ALPINE_GLIBC_PACKAGE_VERSION/$ALPINE_GLIBC_I18N_PACKAGE_FILENAME"  && \
    apk add --no-cache \
        "$ALPINE_GLIBC_BASE_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_BIN_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_I18N_PACKAGE_FILENAME" && \
    rm "/etc/apk/keys/sgerrand.rsa.pub" && \
    /usr/glibc-compat/bin/localedef --force --inputfile POSIX --charmap UTF-8 "$LANG" || true && \
    echo "export LANG=$LANG" > /etc/profile.d/locale.sh && \
    apk del glibc-i18n && \
    rm \
        "/root/.wget-hsts" \
        "$ALPINE_GLIBC_BASE_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_BIN_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_I18N_PACKAGE_FILENAME"

FROM base-image as build-rs

ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH

WORKDIR /src

RUN apk add --no-cache alpine-sdk bash && \
    wget "https://sh.rustup.rs" -O rustup-init && \
    chmod +x ./rustup-init && \
    ./rustup-init -y --no-modify-path --default-toolchain stable --default-host x86_64-unknown-linux-musl && \
    rm -rf rustup-init && \
    wget "https://github.com/PyO3/maturin/releases/download/v0.8.3/maturin-v0.8.3-x86_64-unknown-linux-musl.tar.gz" -O maturin.tar.gz && \
    tar -C /usr/local/cargo/bin -zxf maturin.tar.gz && \
    rm -rf maturin.tar.gz

COPY Cargo.toml Cargo.lock README.md ./
COPY src/ ./src
COPY celery_exporter/  ./celery_exporter/

RUN RUSTFLAGS="-C target-feature=-crt-static" maturin build --target x86_64-unknown-linux-musl --release --manylinux off -o /src/wheelhouse

FROM base-image as app
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

COPY --from=build-rs /src/wheelhouse/ /app/wheelhouse/

COPY requirements/ ./requirements
RUN pip install -r ./requirements/requirements.txt

RUN pip install wheelhouse/*

ENTRYPOINT ["celery-exporter"]
CMD []

EXPOSE 9540
