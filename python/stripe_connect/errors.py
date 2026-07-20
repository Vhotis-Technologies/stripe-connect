"""Public error types for the Stripe Connect engine."""

from __future__ import annotations

from typing import Any, Mapping


class StripeConnectError(Exception):
    """Base error for all stripe-connect failures."""


class ConfigurationError(StripeConnectError):
    """Invalid or incomplete package configuration."""


class AccountError(StripeConnectError):
    """Connected account create/retrieve failures."""


class OnboardingError(StripeConnectError):
    """Account Link / onboarding failures."""


class PaymentError(StripeConnectError):
    """Destination PaymentIntent failures."""


class WebhookError(StripeConnectError):
    """Webhook verification or parsing failures."""


class WebhookSignatureError(WebhookError):
    """Stripe signature header could not be verified."""


class UnsupportedEventError(WebhookError):
    """Reserved for callers that require a specific event type."""


class StripeAPIError(StripeConnectError):
    """Normalized wrapper around a Stripe API / SDK error."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        http_status: int | None = None,
        request_id: str | None = None,
        raw: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.request_id = request_id
        self.raw = raw
