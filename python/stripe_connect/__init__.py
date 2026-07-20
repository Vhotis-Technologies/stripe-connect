"""App-agnostic Stripe Connect engine (v0.1 public API)."""

from stripe_connect.client import ConnectClient, create_client
from stripe_connect.config import StripeConnectConfig
from stripe_connect.errors import (
    AccountError,
    ConfigurationError,
    OnboardingError,
    PaymentError,
    StripeAPIError,
    StripeConnectError,
    UnsupportedEventError,
    WebhookError,
    WebhookSignatureError,
)
from stripe_connect.types import (
    AccountCapabilityState,
    ConnectedAccount,
    DestinationPayment,
    OnboardingLink,
    ParsedWebhookEvent,
    Readiness,
    WebhookEventType,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # Config / client
    "StripeConnectConfig",
    "ConnectClient",
    "create_client",
    # Types
    "AccountCapabilityState",
    "ConnectedAccount",
    "DestinationPayment",
    "OnboardingLink",
    "ParsedWebhookEvent",
    "Readiness",
    "WebhookEventType",
    # Errors
    "StripeConnectError",
    "ConfigurationError",
    "AccountError",
    "OnboardingError",
    "PaymentError",
    "WebhookError",
    "WebhookSignatureError",
    "UnsupportedEventError",
    "StripeAPIError",
]
