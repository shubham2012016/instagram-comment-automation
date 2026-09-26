import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

from automation.models import InstagramAccount, InstagramPost, ProcessedComment

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.instagram.com"
GRAPH_VERSION = getattr(settings, "META_GRAPH_VERSION", "v26.0")


def exchange_code_for_short_token(code: str) -> dict:
    response = requests.post(
        "https://api.instagram.com/oauth/access_token",
        data={
            "client_id": settings.INSTAGRAM_APP_ID,
            "client_secret": settings.INSTAGRAM_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
            "code": code,
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def exchange_for_long_lived_token(short_token: str) -> dict:
    response = requests.get(
        f"{GRAPH_BASE}/access_token",
        params={
            "grant_type": "ig_exchange_token",
            "client_secret": settings.INSTAGRAM_APP_SECRET,
            "access_token": short_token,
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def subscribe_account(account: InstagramAccount) -> dict:
    response = requests.post(
        f"{GRAPH_BASE}/{GRAPH_VERSION}/{account.ig_user_id}/subscribed_apps",
        params={
            "subscribed_fields": "comments",
            "access_token": account.access_token,
        },
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(
            f"Instagram webhook subscription failed ({response.status_code}): "
            f"{response.text[:2000]}"
        )
    return response.json()


def get_profile(access_token: str) -> dict:
    response = requests.get(
        f"{GRAPH_BASE}/{GRAPH_VERSION}/me",
        params={
            "fields": "id,username",
            "access_token": access_token,
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def connect_account(code: str) -> InstagramAccount:
    short = exchange_code_for_short_token(code)
    long_lived = exchange_for_long_lived_token(short["access_token"])
    profile = get_profile(long_lived["access_token"])

    expires_at = None
    if long_lived.get("expires_in"):
        expires_at = timezone.now() + timedelta(seconds=int(long_lived["expires_in"]))

    account, _ = InstagramAccount.objects.update_or_create(
        ig_user_id=str(profile["id"]),
        defaults={
            "username": profile.get("username", ""),
            "access_token": long_lived["access_token"],
            "token_expires_at": expires_at,
            "active": True,
        },
    )

    # Connect this specific Instagram professional account to the
    # app-level webhook subscription already configured in Meta.
    subscribe_account(account)

    return account


def send_private_reply(account: InstagramAccount, comment_id: str, text: str) -> str:
    response = requests.post(
        f"{GRAPH_BASE}/{GRAPH_VERSION}/{account.ig_user_id}/messages",
        params={"access_token": account.access_token},
        json={
            "recipient": {"comment_id": comment_id},
            "message": {"text": text},
        },
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(
            f"Instagram private reply failed ({response.status_code}): {response.text[:2000]}"
        )

    data = response.json()
    return str(data.get("message_id", ""))


def process_comment(
    account: InstagramAccount,
    *,
    comment_id: str,
    media_id: str,
    commenter_id: str = "",
    commenter_username: str = "",
    text: str = "",
) -> ProcessedComment:
    existing = ProcessedComment.objects.filter(comment_id=comment_id).first()
    if existing:
        return existing

    post = InstagramPost.objects.filter(
        account=account,
        media_id=media_id,
        active=True,
        product__active=True,
    ).select_related("product").first()

    record = ProcessedComment.objects.create(
        comment_id=comment_id,
        account=account,
        post=post,
        commenter_id=commenter_id,
        commenter_username=commenter_username,
        text=text,
        status="received",
    )

    if not post:
        record.status = "ignored_no_mapping"
        record.save(update_fields=["status"])
        return record

    reply = f"{post.product.reply_text.strip()}\n{post.product.product_url}"

    try:
        message_id = send_private_reply(account, comment_id, reply)
        record.reply_message_id = message_id
        record.status = "replied"
        record.replied_at = timezone.now()
        record.save(update_fields=["reply_message_id", "status", "replied_at"])
    except Exception as exc:
        logger.exception("Instagram private reply failed for %s", comment_id)
        record.status = "failed"
        record.error_message = str(exc)
        record.save(update_fields=["status", "error_message"])

    return record
