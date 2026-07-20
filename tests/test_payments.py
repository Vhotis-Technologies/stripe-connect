"""Destination payment tests with a mocked Stripe client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from stripe._error import InvalidRequestError

from stripe_connect import ConnectClient, PaymentError, StripeConnectConfig


def _config() -> StripeConnectConfig:
    return StripeConnectConfig(secret_key="sk_test_x", webhook_secret="whsec_x")


def _pi_payload(**overrides: object) -> dict:
    data: dict = {
        "id": "pi_123",
        "client_secret": "pi_123_secret",
        "status": "requires_payment_method",
        "amount": 10_000,
        "currency": "gbp",
        "application_fee_amount": 250,
        "transfer_data": {"destination": "acct_seller"},
    }
    data.update(overrides)
    return data


def test_create_destination_payment_success() -> None:
    stripe = MagicMock()
    stripe.v1.payment_intents.create.return_value = _pi_payload()
    client = ConnectClient(_config(), stripe_client=stripe)

    payment = client.create_destination_payment(
        amount_cents=10_000,
        currency="GBP",
        connected_account_id="acct_seller",
        application_fee_cents=250,
        metadata={"order_id": "1001"},
        idempotency_key="order-1001",
    )

    assert payment.payment_intent_id == "pi_123"
    assert payment.client_secret == "pi_123_secret"
    assert payment.application_fee_amount == 250
    assert payment.transfer_data_destination == "acct_seller"
    assert payment.currency == "gbp"

    args = stripe.v1.payment_intents.create.call_args
    params = args.args[0]
    options = args.args[1]
    assert params["amount"] == 10_000
    assert params["currency"] == "gbp"
    assert params["application_fee_amount"] == 250
    assert params["transfer_data"] == {"destination": "acct_seller"}
    assert "on_behalf_of" not in params
    assert params["metadata"] == {"order_id": "1001"}
    assert options == {"idempotency_key": "order-1001"}


def test_create_destination_payment_without_idempotency() -> None:
    stripe = MagicMock()
    stripe.v1.payment_intents.create.return_value = _pi_payload()
    client = ConnectClient(_config(), stripe_client=stripe)

    client.create_destination_payment(
        amount_cents=1000,
        currency="gbp",
        connected_account_id="acct_seller",
        application_fee_cents=25,
    )

    assert len(stripe.v1.payment_intents.create.call_args.args) == 1


def test_create_destination_payment_validation() -> None:
    client = ConnectClient(_config(), stripe_client=MagicMock())

    with pytest.raises(PaymentError, match="amount_cents"):
        client.create_destination_payment(
            amount_cents=0,
            currency="gbp",
            connected_account_id="acct_seller",
            application_fee_cents=0,
        )
    with pytest.raises(PaymentError, match="application_fee_cents must be less"):
        client.create_destination_payment(
            amount_cents=100,
            currency="gbp",
            connected_account_id="acct_seller",
            application_fee_cents=100,
        )
    with pytest.raises(PaymentError, match="application_fee_cents must be a non-negative"):
        client.create_destination_payment(
            amount_cents=100,
            currency="gbp",
            connected_account_id="acct_seller",
            application_fee_cents=-1,
        )
    with pytest.raises(PaymentError, match="connected_account_id"):
        client.create_destination_payment(
            amount_cents=100,
            currency="gbp",
            connected_account_id="",
            application_fee_cents=1,
        )


def test_create_destination_payment_wraps_stripe_error() -> None:
    stripe = MagicMock()
    stripe.v1.payment_intents.create.side_effect = InvalidRequestError(
        message="No such destination: acct_missing",
        param="transfer_data[destination]",
        code="resource_missing",
    )
    client = ConnectClient(_config(), stripe_client=stripe)

    with pytest.raises(PaymentError, match="No such destination") as exc_info:
        client.create_destination_payment(
            amount_cents=1000,
            currency="gbp",
            connected_account_id="acct_missing",
            application_fee_cents=25,
        )
    assert exc_info.value.__cause__ is not None
    assert exc_info.value.__cause__.code == "resource_missing"
