"""Normalization helpers for Stripe Account / AccountLink payloads."""

from __future__ import annotations

from stripe_connect._stripe import normalize_account, normalize_onboarding_link


def test_normalize_account_from_dict() -> None:
    account = normalize_account(
        {
            "id": "acct_1",
            "email": "a@b.com",
            "country": "GB",
            "type": "express",
            "charges_enabled": True,
            "payouts_enabled": False,
            "details_submitted": True,
            "requirements": {
                "currently_due": ["tos_acceptance.date"],
                "past_due": [],
                "disabled_reason": None,
            },
            "metadata": {"entity_id": 99},
        }
    )
    assert account.id == "acct_1"
    assert account.charges_enabled is True
    assert account.payouts_enabled is False
    assert account.requirements_currently_due == ("tos_acceptance.date",)
    assert account.metadata["entity_id"] == "99"


def test_normalize_onboarding_link_from_dict() -> None:
    link = normalize_onboarding_link({"url": "https://example.com/link", "expires_at": 123})
    assert link.url == "https://example.com/link"
    assert link.expires_at == 123


def test_normalize_destination_payment_from_dict() -> None:
    from stripe_connect._stripe import normalize_destination_payment

    payment = normalize_destination_payment(
        {
            "id": "pi_1",
            "client_secret": "sec",
            "status": "succeeded",
            "amount": 500,
            "currency": "USD",
            "application_fee_amount": 12,
            "transfer_data": {"destination": "acct_x"},
        }
    )
    assert payment.payment_intent_id == "pi_1"
    assert payment.currency == "usd"
    assert payment.transfer_data_destination == "acct_x"
