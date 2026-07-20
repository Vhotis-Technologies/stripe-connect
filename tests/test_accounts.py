"""Account create/retrieve tests with a mocked Stripe client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from stripe._error import InvalidRequestError

from stripe_connect import AccountError, ConnectClient, StripeConnectConfig, create_client
from stripe_connect.types import AccountCapabilityState


def _config() -> StripeConnectConfig:
    return StripeConnectConfig(secret_key="sk_test_x", webhook_secret="whsec_x")


def _account_payload(**overrides: object) -> dict:
    data: dict = {
        "id": "acct_123",
        "email": "seller@example.com",
        "country": "GB",
        "type": "express",
        "charges_enabled": False,
        "payouts_enabled": False,
        "details_submitted": False,
        "requirements": {
            "currently_due": ["business_profile.url"],
            "past_due": [],
            "disabled_reason": None,
        },
        "metadata": {"app": "vhotis", "entity_id": "42"},
    }
    data.update(overrides)
    return data


def test_create_express_account_success() -> None:
    stripe = MagicMock()
    stripe.v1.accounts.create.return_value = _account_payload()
    client = ConnectClient(_config(), stripe_client=stripe)

    account = client.create_express_account(
        email="seller@example.com",
        country="gb",
        metadata={"app": "vhotis", "entity_id": "42"},
    )

    assert account.id == "acct_123"
    assert account.type == "express"
    assert account.metadata["entity_id"] == "42"
    assert account.charges_enabled is False
    stripe.v1.accounts.create.assert_called_once()
    params = stripe.v1.accounts.create.call_args.args[0]
    assert params["type"] == "express"
    assert params["country"] == "GB"
    assert params["capabilities"]["card_payments"]["requested"] is True
    assert params["capabilities"]["transfers"]["requested"] is True


def test_create_express_account_passes_optional_fields() -> None:
    stripe = MagicMock()
    stripe.v1.accounts.create.return_value = _account_payload()
    client = ConnectClient(_config(), stripe_client=stripe)

    client.create_express_account(
        email="seller@example.com",
        country="US",
        metadata={},
        business_type="individual",
        capabilities={"transfers": {"requested": True}},
    )

    params = stripe.v1.accounts.create.call_args.args[0]
    assert params["business_type"] == "individual"
    assert params["capabilities"] == {"transfers": {"requested": True}}


def test_create_express_account_wraps_stripe_error() -> None:
    stripe = MagicMock()
    stripe.v1.accounts.create.side_effect = InvalidRequestError(
        message="bad request",
        param=None,
        code="parameter_invalid_empty",
    )
    client = ConnectClient(_config(), stripe_client=stripe)

    with pytest.raises(AccountError, match="bad request") as exc_info:
        client.create_express_account(
            email="seller@example.com",
            country="GB",
            metadata={},
        )
    assert exc_info.value.__cause__ is not None
    assert exc_info.value.__cause__.code == "parameter_invalid_empty"


def test_retrieve_account_and_is_ready() -> None:
    stripe = MagicMock()
    stripe.v1.accounts.retrieve.return_value = _account_payload(
        charges_enabled=True,
        payouts_enabled=True,
        details_submitted=True,
        requirements={"currently_due": [], "past_due": [], "disabled_reason": None},
    )
    client = ConnectClient(_config(), stripe_client=stripe)

    account = client.retrieve_account("acct_123")
    assert account.id == "acct_123"

    readiness = client.is_ready("acct_123")
    assert readiness.is_ready is True
    assert readiness.status is AccountCapabilityState.READY
    stripe.v1.accounts.retrieve.assert_called()


def test_is_ready_pending_when_flags_false() -> None:
    stripe = MagicMock()
    stripe.v1.accounts.retrieve.return_value = _account_payload()
    client = ConnectClient(_config(), stripe_client=stripe)

    readiness = client.is_ready("acct_123")
    assert readiness.is_ready is False
    assert readiness.status is AccountCapabilityState.PENDING


def test_is_ready_restricted_when_disabled() -> None:
    stripe = MagicMock()
    stripe.v1.accounts.retrieve.return_value = _account_payload(
        requirements={
            "currently_due": [],
            "past_due": ["individual.verification.document"],
            "disabled_reason": "requirements.past_due",
        }
    )
    client = ConnectClient(_config(), stripe_client=stripe)

    readiness = client.is_ready("acct_123")
    assert readiness.is_ready is False
    assert readiness.status is AccountCapabilityState.RESTRICTED
    assert readiness.disabled_reason == "requirements.past_due"


def test_create_client_factory_still_works() -> None:
    client = create_client(_config())
    assert isinstance(client, ConnectClient)
