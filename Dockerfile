FROM python:3.6-stretch as build-rs

ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH

WORKDIR /src

RUN set -eux; \
    \
    url="https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init"; \
    wget "$url"; \
    chmod +x rustup-init; \
    ./rustup-init -y --no-modify-path --default-toolchain nightly; \
    rm rustup-init; \
    chmod -R a+w $RUSTUP_HOME $CARGO_HOME; \
    rustup --version; \
    cargo --version; \
    rustc --version; \
    rustup toolchain install nightly-2019-06-20; \
    rustup default nightly-2019-06-20

RUN pip install pyo3-pack==0.6.1

COPY Cargo.toml Cargo.lock setup.py README.md ./
COPY src/ ./src

RUN pyo3-pack  build --release -i python3 --out ./

FROM python:3.6-stretch

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

COPY --from=build-rs /src/celery_state-0.1.0-cp36-cp36m-manylinux1_x86_64.whl .

COPY requirements/ ./requirements
RUN pip install -r ./requirements/requirements.txt

COPY  setup.py README.md ./
COPY celery_exporter/  ./celery_exporter/

RUN pip install *.whl
RUN pip install --no-deps -e .

ENTRYPOINT ["celery-exporter"]
CMD []

EXPOSE 9540
