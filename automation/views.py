import hashlib
import hmac
import json
import logging
import secrets
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

from .models import InstagramAccount
from .services.instagram import connect_account, process_comment

logger = logging.getLogger(__name__)


def instagram_connect(request):
    state = secrets.token_urlsafe(32)
    request.session["instagram_oauth_state"] = state

    params = {
        "client_id": settings.INSTAGRAM_APP_ID,
        "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
        "response_type": "code",
        "scope": ",".join(settings.INSTAGRAM_OAUTH_SCOPES),
        "state": state,
        "enable_fb_login": "0",
    }

    url = "https://www.instagram.com/oauth/authorize?" + urlencode(params)
    return redirect(url)


def instagram_callback(request):
    error = request.GET.get("error")
    if error:
        return JsonResponse(
            {
                "ok": False,
                "error": error,
                "description": request.GET.get("error_description", ""),
            },
            status=400,
        )

    state = request.GET.get("state", "")
    expected_state = request.session.pop("instagram_oauth_state", "")
    if not expected_state or not secrets.compare_digest(state, expected_state):
        return JsonResponse({"ok": False, "error": "Invalid OAuth state."}, status=400)

    code = request.GET.get("code")
    if not code:
        return JsonResponse({"ok": False, "error": "Missing authorization code."}, status=400)

    try:
        account = connect_account(code)
    except Exception as exc:
        logger.exception("Instagram OAuth callback failed")
        return JsonResponse(
            {"ok": False, "error": "Instagram connection failed.", "detail": str(exc)},
            status=502,
        )

    return JsonResponse(
        {
            "ok": True,
            "message": "Instagram account connected.",
            "ig_user_id": account.ig_user_id,
            "username": account.username,
        }
    )


def _verify_signature(request) -> bool:
    app_secret = getattr(settings, "INSTAGRAM_APP_SECRET", "")
    if not app_secret:
        return True

    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature.startswith("sha256="):
        return False

    expected = hmac.new(
        app_secret.encode(),
        request.body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature[7:], expected)


def _extract_comment_events(payload):
    events = []

    for entry in payload.get("entry", []):
        account_id = str(entry.get("id", ""))

        # Meta can deliver multiple changes in one webhook request.
        for change in entry.get("changes", []):
            if change.get("field") != "comments":
                continue

            value = change.get("value", {})
            events.append(
                {
                    "account_id": account_id,
                    "comment_id": str(
                        value.get("id")
                        or value.get("comment_id")
                        or ""
                    ),
                    "media_id": str(
                        value.get("media", {}).get("id")
                        if isinstance(value.get("media"), dict)
                        else value.get("media_id")
                        or value.get("media", "")
                    ),
                    "commenter_id": str(
                        value.get("from", {}).get("id")
                        if isinstance(value.get("from"), dict)
                        else value.get("from_id")
                        or ""
                    ),
                    "commenter_username": str(
                        value.get("from", {}).get("username")
                        if isinstance(value.get("from"), dict)
                        else value.get("username")
                        or ""
                    ),
                    "text": str(value.get("text", "")),
                }
            )

    return [event for event in events if event["account_id"] and event["comment_id"]]


@csrf_exempt
def instagram_webhook(request):
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == settings.META_WEBHOOK_VERIFY_TOKEN:
            return HttpResponse(challenge or "", status=200, content_type="text/plain")

        return HttpResponse("Forbidden", status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not _verify_signature(request):
        return JsonResponse({"error": "Invalid signature"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    logger.info("Instagram webhook payload received: %s", payload)

    for event in _extract_comment_events(payload):
        account = InstagramAccount.objects.filter(
            ig_user_id=event["account_id"],
            active=True,
        ).first()

        if not account:
            logger.warning(
                "Ignoring comment %s: Instagram account %s is not connected.",
                event["comment_id"],
                event["account_id"],
            )
            continue

        process_comment(
            account,
            comment_id=event["comment_id"],
            media_id=event["media_id"],
            commenter_id=event["commenter_id"],
            commenter_username=event["commenter_username"],
            text=event["text"],
        )

    return JsonResponse({"status": "received"})


