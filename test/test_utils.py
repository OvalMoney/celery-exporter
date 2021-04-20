import ssl
import pytest

from celery_exporter.utils import get_transport_scheme, generate_broker_use_ssl


@pytest.mark.parametrize("brokers", [("redis://foo", "redis"), ("amqp://bar", "amqp")])
def test_get_transport_scheme(brokers):
    assert get_transport_scheme(brokers[0]) == brokers[1]


def test_generate_broker_use_ssl_no_ssl():
    assert (
        generate_broker_use_ssl(
            False, "redis", "CERT_NONE", "path/ca.pem", "path/cert.pem", "path/key.pem"
        )
        == None
    )


def test_generate_broker_use_ssl_exception():
    with pytest.raises(ValueError):
        generate_broker_use_ssl(
            True, "wrong", "CERT_NONE", "path/ca.pem", "path/cert.pem", "path/key.pem"
        )

    with pytest.raises(ValueError):
        generate_broker_use_ssl(
            True,
            "redis",
            "WRONG_VERIFY",
            "path/ca.pem",
            "path/cert.pem",
            "path/key.pem",
        )


def test_generate_broker_use_ssl():
    assert generate_broker_use_ssl(
        True, "redis", "CERT_NONE", "path/ca.pem", "path/cert.pem", "path/key.pem"
    ) == {
        "ssl_keyfile": "path/key.pem",
        "ssl_certfile": "path/cert.pem",
        "ssl_ca_certs": "path/ca.pem",
        "ssl_cert_reqs": ssl.CERT_NONE,
    }

    assert generate_broker_use_ssl(
        True, "amqp", "CERT_OPTIONAL", "path/ca.pem", "path/cert.pem", "path/key.pem"
    ) == {
        "keyfile": "path/key.pem",
        "certfile": "path/cert.pem",
        "ca_certs": "path/ca.pem",
        "cert_reqs": ssl.CERT_OPTIONAL,
    }

    assert generate_broker_use_ssl(
        True, "amqp", "CERT_REQUIRED", "path/ca.pem", "path/cert.pem", "path/key.pem"
    ) == {
        "keyfile": "path/key.pem",
        "certfile": "path/cert.pem",
        "ca_certs": "path/ca.pem",
        "cert_reqs": ssl.CERT_REQUIRED,
    }
