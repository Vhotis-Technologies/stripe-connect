"""Connect webhook verification and normalization."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from stripe import Webhook
from stripe._error import SignatureVerificationError

from stripe_connect._stripe import _as_raw_mapping, _get, normalize_account
from stripe_connect.errors import WebhookError, WebhookSignatureError
from stripe_connect.types import ParsedWebhookEvent, WebhookEventType

if TYPE_CHECKING:
    from stripe_connect.client import ConnectClient


def parse_webhook(
    client: ConnectClient,
    payload: bytes | str,
    sig_header: str,
) -> ParsedWebhookEvent:
    """Verify the Stripe signature and return a normalized event.

    At least ``account.updated`` is normalized into ``data`` as a
    :class:`~stripe_connect.types.ConnectedAccount`. Other types return
    ``WebhookEventType.UNKNOWN`` with ``data=None`` and the raw payload.
    """
    if payload is None:
        raise WebhookError("payload is required")
    if not sig_header or not str(sig_header).strip():
        raise WebhookSignatureError("sig_header must be a non-empty string")

    try:
        event = Webhook.construct_event(
            payload,
            sig_header,
            client.config.webhook_secret,
        )
    except SignatureVerificationError as exc:
        raise WebhookSignatureError("Webhook signature verification failed") from exc
    except ValueError as exc:
        raise WebhookError(f"Invalid webhook payload: {exc}") from exc
    except Exception as exc:
        raise WebhookError(f"Failed to parse webhook: {exc}") from exc

    return normalize_webhook_event(event)


def normalize_webhook_event(event: Any) -> ParsedWebhookEvent:
    """Normalize a verified Stripe Event object/dict."""
    event_id = _get(event, "id")
    if not event_id:
        raise WebhookError("Stripe event missing id")

    type_raw = str(_get(event, "type") or "")
    account_id = _get(event, "account")
    livemode = bool(_get(event, "livemode", False))
    created = int(_get(event, "created") or 0)
    raw = _as_raw_mapping(event)

    if type_raw == WebhookEventType.ACCOUNT_UPDATED.value:
        data_wrapper = _get(event, "data") or {}
        obj = _get(data_wrapper, "object")
        if obj is None:
            raise WebhookError("account.updated event missing data.object")
        try:
            connected = normalize_account(obj)
        except ValueError as exc:
            raise WebhookError(str(exc)) from exc
        return ParsedWebhookEvent(
            id=str(event_id),
            type=WebhookEventType.ACCOUNT_UPDATED,
            type_raw=type_raw,
            account_id=str(account_id) if account_id else connected.id,
            livemode=livemode,
            created=created,
            data=connected,
            raw=raw,
        )

    return ParsedWebhookEvent(
        id=str(event_id),
        type=WebhookEventType.UNKNOWN,
        type_raw=type_raw,
        account_id=str(account_id) if account_id else None,
        livemode=livemode,
        created=created,
        data=None,
        raw=raw,
    )
