"""Phase 1/2 contract tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from stripe_connect import (
    AccountCapabilityState,
    AccountError,
    ConnectClient,
    StripeConnectConfig,
    WebhookEventType,
    __version__,
    create_client,
)


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_config_accepts_valid_values() -> None:
    config = StripeConnectConfig(
        secret_key="sk_test_x",
        webhook_secret="whsec_x",
        default_country="GB",
    )
    assert config.api_version is None
    assert config.default_country == "GB"


def test_config_rejects_empty_secret() -> None:
    with pytest.raises(ValueError, match="secret_key"):
        StripeConnectConfig(secret_key="", webhook_secret="whsec_x")


def test_config_rejects_bad_country() -> None:
    with pytest.raises(ValueError, match="default_country"):
        StripeConnectConfig(secret_key="sk_test_x", webhook_secret="whsec_x", default_country="GBR")


def test_create_client() -> None:
    client = create_client(
        StripeConnectConfig(secret_key="sk_test_x", webhook_secret="whsec_x")
    )
    assert isinstance(client, ConnectClient)
    assert client.config.secret_key == "sk_test_x"
    assert client.stripe is not None


def test_create_client_accepts_injected_stripe_client() -> None:
    fake = MagicMock(name="StripeClient")
    client = ConnectClient(
        StripeConnectConfig(secret_key="sk_test_x", webhook_secret="whsec_x"),
        stripe_client=fake,
    )
    assert client.stripe is fake


def test_enums_stable_for_adapters() -> None:
    assert AccountCapabilityState.READY.value == "ready"
    assert AccountCapabilityState.NOT_STARTED.value == "not_started"
    assert WebhookEventType.ACCOUNT_UPDATED.value == "account.updated"


def test_account_validation_errors() -> None:
    client = create_client(
        StripeConnectConfig(secret_key="sk_test_x", webhook_secret="whsec_x")
    )
    with pytest.raises(AccountError, match="email"):
        client.create_express_account(email=" ", country="GB", metadata={})
    with pytest.raises(AccountError, match="country"):
        client.create_express_account(email="a@b.com", country="GBR", metadata={})
    with pytest.raises(AccountError, match="account_id"):
        client.retrieve_account("")
