import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger(__name__)


@csrf_exempt
def instagram_webhook(request):
    """
    Meta Instagram webhook endpoint.

    GET:
        Used by Meta to verify the webhook.

    POST:
        Receives Instagram webhook events.
    """

    # ---------------------------------------------------------
    # META WEBHOOK VERIFICATION
    # ---------------------------------------------------------
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        verify_token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        expected_token = settings.META_WEBHOOK_VERIFY_TOKEN

        if (
            mode == "subscribe"
            and verify_token
            and hmac.compare_digest(verify_token, expected_token)
        ):
            return HttpResponse(challenge, status=200)

        return HttpResponse("Forbidden", status=403)

    # ---------------------------------------------------------
    # WEBHOOK EVENT
    # ---------------------------------------------------------
    if request.method == "POST":

        # Verify Meta signature when App Secret is configured.
        app_secret = settings.META_APP_SECRET

        if app_secret:
            signature = request.headers.get("X-Hub-Signature-256", "")

            if not signature.startswith("sha256="):
                return HttpResponse("Invalid signature", status=403)

            expected_signature = hmac.new(
                app_secret.encode("utf-8"),
                request.body,
                hashlib.sha256,
            ).hexdigest()

            received_signature = signature.split("=", 1)[1]

            if not hmac.compare_digest(
                expected_signature,
                received_signature,
            ):
                return HttpResponse("Invalid signature", status=403)

        try:
            payload = json.loads(request.body)

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON"},
                status=400,
            )

        logger.info(
            "Instagram webhook received: %s",
            json.dumps(payload, ensure_ascii=False),
        )

        # -----------------------------------------------------
        # IMPORTANT:
        # We will process comments here later.
        # -----------------------------------------------------

        return JsonResponse(
            {
                "status": "received",
            },
            status=200,
        )

    return HttpResponse(
        "Method Not Allowed",
        status=405,
    )