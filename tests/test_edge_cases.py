"""Extra edge-case coverage for v0.1 hardening."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from stripe_connect import ConnectClient, PaymentError, StripeConnectConfig
from stripe_connect._stripe import normalize_account
from stripe_connect.types import AccountCapabilityState
from stripe_connect.webhooks import normalize_webhook_event


def _config() -> StripeConnectConfig:
    return StripeConnectConfig(secret_key="sk_test_x", webhook_secret="whsec_x")


def test_normalize_account_missing_requirements_block() -> None:
    account = normalize_account(
        {
            "id": "acct_bare",
            "type": "express",
            "charges_enabled": False,
            "payouts_enabled": False,
            "details_submitted": False,
        }
    )
    assert account.requirements_currently_due == ()
    assert account.requirements_past_due == ()
    assert account.requirements_disabled_reason is None
    assert account.metadata == {}


def test_create_express_account_empty_metadata() -> None:
    stripe = MagicMock()
    stripe.v1.accounts.create.return_value = {
        "id": "acct_empty_meta",
        "type": "express",
        "charges_enabled": False,
        "payouts_enabled": False,
        "details_submitted": False,
        "metadata": {},
    }
    client = ConnectClient(_config(), stripe_client=stripe)
    account = client.create_express_account(
        email="a@b.com",
        country="GB",
        metadata={},
    )
    assert account.id == "acct_empty_meta"
    params = stripe.v1.accounts.create.call_args.args[0]
    assert params["metadata"] == {}


def test_zero_application_fee_allowed() -> None:
    stripe = MagicMock()
    stripe.v1.payment_intents.create.return_value = {
        "id": "pi_zero_fee",
        "client_secret": "sec",
        "status": "requires_payment_method",
        "amount": 1000,
        "currency": "gbp",
        "application_fee_amount": 0,
        "transfer_data": {"destination": "acct_seller"},
    }
    client = ConnectClient(_config(), stripe_client=stripe)
    payment = client.create_destination_payment(
        amount_cents=1000,
        currency="gbp",
        connected_account_id="acct_seller",
        application_fee_cents=0,
    )
    assert payment.application_fee_amount == 0


def test_fee_equal_to_amount_rejected() -> None:
    client = ConnectClient(_config(), stripe_client=MagicMock())
    with pytest.raises(PaymentError, match="less than amount_cents"):
        client.create_destination_payment(
            amount_cents=500,
            currency="gbp",
            connected_account_id="acct_seller",
            application_fee_cents=500,
        )


def test_account_updated_falls_back_to_object_id() -> None:
    parsed = normalize_webhook_event(
        {
            "id": "evt_no_account_field",
            "type": "account.updated",
            "livemode": False,
            "created": 1,
            "data": {
                "object": {
                    "id": "acct_from_object",
                    "type": "express",
                    "charges_enabled": False,
                    "payouts_enabled": False,
                    "details_submitted": False,
                    "requirements": {
                        "currently_due": [],
                        "past_due": ["individual.verification.document"],
                        "disabled_reason": "requirements.past_due",
                    },
                    "metadata": {},
                }
            },
        }
    )
    assert parsed.account_id == "acct_from_object"
    assert parsed.data is not None
    readiness_status = parsed.data  # ConnectedAccount flags for adapter
    assert readiness_status.charges_enabled is False
    from stripe_connect.readiness import from_account

    readiness = from_account(parsed.data)
    assert readiness.status is AccountCapabilityState.RESTRICTED


def test_public_exports_importable() -> None:
    import stripe_connect as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), name
