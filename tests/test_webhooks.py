"""Webhook parse/normalize tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from stripe._error import SignatureVerificationError

from stripe_connect import (
    ConnectClient,
    StripeConnectConfig,
    WebhookError,
    WebhookEventType,
    WebhookSignatureError,
)
from stripe_connect.webhooks import normalize_webhook_event


def _config() -> StripeConnectConfig:
    return StripeConnectConfig(secret_key="sk_test_x", webhook_secret="whsec_test")


def _account_updated_event(**overrides: object) -> dict:
    data: dict = {
        "id": "evt_123",
        "type": "account.updated",
        "account": "acct_123",
        "livemode": False,
        "created": 1_700_000_000,
        "data": {
            "object": {
                "id": "acct_123",
                "email": "seller@example.com",
                "country": "GB",
                "type": "express",
                "charges_enabled": True,
                "payouts_enabled": True,
                "details_submitted": True,
                "requirements": {
                    "currently_due": [],
                    "past_due": [],
                    "disabled_reason": None,
                },
                "metadata": {"entity_id": "42"},
            }
        },
    }
    data.update(overrides)
    return data


def test_normalize_account_updated() -> None:
    parsed = normalize_webhook_event(_account_updated_event())
    assert parsed.type is WebhookEventType.ACCOUNT_UPDATED
    assert parsed.account_id == "acct_123"
    assert parsed.data is not None
    assert parsed.data.charges_enabled is True
    assert parsed.data.payouts_enabled is True
    assert parsed.data.metadata["entity_id"] == "42"


def test_normalize_unknown_event() -> None:
    parsed = normalize_webhook_event(
        {
            "id": "evt_other",
            "type": "payment_intent.succeeded",
            "account": None,
            "livemode": True,
            "created": 1,
            "data": {"object": {"id": "pi_1"}},
        }
    )
    assert parsed.type is WebhookEventType.UNKNOWN
    assert parsed.type_raw == "payment_intent.succeeded"
    assert parsed.data is None
    assert parsed.livemode is True


def test_parse_webhook_success() -> None:
    stripe = MagicMock()
    client = ConnectClient(_config(), stripe_client=stripe)
    event = _account_updated_event()

    with patch("stripe_connect.webhooks.Webhook.construct_event", return_value=event) as construct:
        parsed = client.parse_webhook(b'{"id":"evt_123"}', "t=1,v1=abc")

    construct.assert_called_once_with(b'{"id":"evt_123"}', "t=1,v1=abc", "whsec_test")
    assert parsed.type is WebhookEventType.ACCOUNT_UPDATED
    assert parsed.id == "evt_123"


def test_parse_webhook_signature_failure() -> None:
    client = ConnectClient(_config(), stripe_client=MagicMock())

    with patch(
        "stripe_connect.webhooks.Webhook.construct_event",
        side_effect=SignatureVerificationError("bad sig", sig_header="t=1,v1=bad"),
    ):
        with pytest.raises(WebhookSignatureError, match="signature"):
            client.parse_webhook(b"{}", "t=1,v1=bad")


def test_parse_webhook_invalid_payload() -> None:
    client = ConnectClient(_config(), stripe_client=MagicMock())

    with patch(
        "stripe_connect.webhooks.Webhook.construct_event",
        side_effect=ValueError("Invalid payload"),
    ):
        with pytest.raises(WebhookError, match="Invalid webhook payload"):
            client.parse_webhook(b"not-json", "t=1,v1=abc")


def test_parse_webhook_requires_sig_header() -> None:
    client = ConnectClient(_config(), stripe_client=MagicMock())
    with pytest.raises(WebhookSignatureError, match="sig_header"):
        client.parse_webhook(b"{}", "")
