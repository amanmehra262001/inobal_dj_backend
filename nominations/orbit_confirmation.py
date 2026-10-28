"""
"Official Selection Confirmation" email for the Worth Minds Orbit Edition.

Sent from media@worthminds.com a set time after a nomination is submitted
(ORBIT_CONFIRMATION_DELAY_HOURS, default 36), by the management command
`python manage.py send_orbit_confirmations`, which a cron job runs every hour.

Who gets it (ORBIT_CONFIRMATION_MODE):
  "auto"    — every nomination that has not been rejected once the delay has passed (default)
  "approve" — only nominations an editor has marked Approved, once the delay has passed

Only nominations submitted on or after ORBIT_CONFIRMATION_START are considered, so turning
this on never emails people who nominated before the feature existed. Nothing is sent until
that setting is present.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date

from .models import Nominations

logger = logging.getLogger(__name__)

DESIGNS = ("letter", "night", "certificate")
MAX_ATTEMPTS = 3


def _setting(name: str, default=None):
    return getattr(settings, name, default)


def subject_for(name: str) -> str:
    return f"{name} | Official Selection Confirmation — Worth Minds Orbit Edition: 30 Stories Beyond Earth"


def proper_name(raw: str) -> str:
    """'vijay LAGARIYA' -> 'Vijay Lagariya' (keeps already mixed-case names such as 'McArthur')."""
    words = []
    for word in raw.split():
        if word.islower() or word.isupper():
            word = "-".join(part[:1].upper() + part[1:].lower() for part in word.split("-"))
        words.append(word)
    return " ".join(words)


def letter_date(when: datetime) -> str:
    local = timezone.localtime(when, timezone.get_fixed_timezone(330))  # IST
    return f"{local.day} {local.strftime('%B %Y')}"


def render(name: str, when: datetime | None = None) -> tuple[str, str, str]:
    """Return (subject, text, html) for one nominee."""
    when = when or timezone.now()
    design = _setting("ORBIT_CONFIRMATION_DESIGN", "letter")
    if design not in DESIGNS:
        design = "letter"
    site_url = _setting("ORBIT_CONFIRMATION_SITE_URL", "https://www.worthminds.com").rstrip("/")
    stamp = "inobal-stamp.png" if _setting("ORBIT_CONFIRMATION_STAMP", "mono") == "color" else "inobal-stamp-mono.png"
    context = {
        "name": name,
        "letter_date": letter_date(when),
        "site_url": site_url,
        "stamp_url": f"{site_url}/images/email/{stamp}",
    }
    html = render_to_string(f"nominations/email/orbit_confirmation_{design}.html", context)
    text = render_to_string("nominations/email/orbit_confirmation.txt", context)
    return subject_for(name), text, html


def media_connection():
    """SMTP connection for media@worthminds.com (separate from any other mail settings)."""
    return get_connection(
        backend=_setting("MEDIA_EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"),
        host=_setting("MEDIA_EMAIL_HOST", "smtp.gmail.com"),
        port=int(_setting("MEDIA_EMAIL_PORT", 465)),
        username=_setting("MEDIA_EMAIL_USER"),
        password=_setting("MEDIA_EMAIL_PASSWORD"),
        use_ssl=int(_setting("MEDIA_EMAIL_PORT", 465)) == 465,
        use_tls=int(_setting("MEDIA_EMAIL_PORT", 465)) == 587,
        timeout=30,
    )


def build_message(to_email: str, name: str, connection=None, when: datetime | None = None) -> EmailMultiAlternatives:
    subject, text, html = render(name, when)
    from_email = _setting("MEDIA_EMAIL_FROM") or f"Worth Minds Magazine <{_setting('MEDIA_EMAIL_USER') or 'media@worthminds.com'}>"
    bcc = [a.strip() for a in (_setting("ORBIT_CONFIRMATION_BCC") or "").split(",") if a.strip()]
    reply_to = [_setting("MEDIA_EMAIL_REPLY_TO") or _setting("MEDIA_EMAIL_USER") or "media@worthminds.com"]
    msg = EmailMultiAlternatives(
        subject=subject, body=text, from_email=from_email, to=[to_email], bcc=bcc,
        reply_to=reply_to, connection=connection,
    )
    msg.attach_alternative(html, "text/html")
    return msg


def relay_ready() -> bool:
    return bool(_setting("MEDIA_EMAIL_RELAY_URL") and _setting("MEDIA_EMAIL_RELAY_SECRET"))


def smtp_ready() -> bool:
    return bool(_setting("MEDIA_EMAIL_USER") and _setting("MEDIA_EMAIL_PASSWORD"))


def deliver(msg: EmailMultiAlternatives) -> None:
    """Send one message: through the website's mail relay when configured, else by SMTP.

    The relay exists because Google refuses SMTP logins from the backend server's address.
    """
    if not relay_ready():
        msg.send(fail_silently=False)
        return
    import requests  # already in requirements.txt

    html = next((body for body, mime in msg.alternatives if mime == "text/html"), "")
    response = requests.post(
        _setting("MEDIA_EMAIL_RELAY_URL"),
        json={"to": msg.to[0], "subject": msg.subject, "html": html, "text": msg.body, "bcc": list(msg.bcc)},
        headers={"Authorization": f"Bearer {_setting('MEDIA_EMAIL_RELAY_SECRET')}"},
        timeout=45,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Mail relay answered {response.status_code}: {response.text[:300]}")


def start_time() -> datetime | None:
    raw = (_setting("ORBIT_CONFIRMATION_START") or "").strip()
    if not raw:
        return None
    value = parse_datetime(raw)
    if value is None:
        day = parse_date(raw)
        if day is None:
            raise ValueError(f"ORBIT_CONFIRMATION_START is not a date: {raw!r}")
        value = datetime(day.year, day.month, day.day)
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_fixed_timezone(330))  # read as IST
    return value


@dataclass
class Result:
    sent: int = 0
    skipped: int = 0
    failed: int = 0
    waiting_for_review: int = 0


def due_queryset(now: datetime | None = None):
    """Nominations whose confirmation is due now (before the mode/review filter)."""
    now = now or timezone.now()
    start = start_time()
    delay = timedelta(hours=float(_setting("ORBIT_CONFIRMATION_DELAY_HOURS", 36)))
    form_id = int(_setting("ORBIT_CONFIRMATION_FORM_ID", 2))
    qs = Nominations.objects.filter(
        form_id=form_id,
        created_at__lte=now - delay,
        confirmation_status__in=[Nominations.ConfirmationStatus.NOT_SENT, Nominations.ConfirmationStatus.FAILED],
        confirmation_attempts__lt=MAX_ATTEMPTS,
    ).exclude(review_status=Nominations.ReviewStatus.REJECTED)
    if start is not None:
        qs = qs.filter(created_at__gte=start)
    return qs.order_by("created_at")


def _mark(nomination_id: int, status: str, note: str, sent: bool = False):
    fields = {"confirmation_status": status, "confirmation_note": note[:2000]}
    if sent:
        fields["confirmation_sent_at"] = timezone.now()
    Nominations.objects.filter(pk=nomination_id).update(**fields)


def send_due(dry_run: bool = False, limit: int | None = None, log=print) -> Result:
    result = Result()
    if start_time() is None:
        log("ORBIT_CONFIRMATION_START is not set: nothing will be sent. Set it to the go-live date (e.g. 2026-11-01).")
        return result
    if not dry_run and not (relay_ready() or smtp_ready()):
        log("No way to send: set MEDIA_EMAIL_RELAY_URL + MEDIA_EMAIL_RELAY_SECRET (or MEDIA_EMAIL_USER + MEDIA_EMAIL_PASSWORD).")
        return result

    approve_mode = _setting("ORBIT_CONFIRMATION_MODE", "auto") == "approve"
    candidates = list(due_queryset()[: limit or None])
    connection = None if (dry_run or relay_ready()) else media_connection()

    for nomination in candidates:
        if approve_mode and nomination.review_status != Nominations.ReviewStatus.APPROVED:
            result.waiting_for_review += 1
            continue

        name = proper_name(nomination.nominee_name)
        email = nomination.nominee_email
        try:
            validate_email(email)
        except ValidationError:
            if not dry_run:
                _mark(nomination.pk, Nominations.ConfirmationStatus.SKIPPED, f"No valid email address ({email!r}).")
            result.skipped += 1
            log(f"#{nomination.pk}: skipped, no valid email")
            continue
        if not name:
            name = "Nominee"

        # Never send twice to the same address for the same form.
        earlier = (
            Nominations.objects.filter(form_id=nomination.form_id, confirmation_status=Nominations.ConfirmationStatus.SENT)
            .exclude(pk=nomination.pk)
            .only("id", "responses")
        )
        duplicate = next((n.pk for n in earlier if n.nominee_email.lower() == email.lower()), None)
        if duplicate:
            if not dry_run:
                _mark(nomination.pk, Nominations.ConfirmationStatus.SKIPPED, f"Already sent for nomination #{duplicate} (same email).")
            result.skipped += 1
            log(f"#{nomination.pk}: skipped, already confirmed as #{duplicate}")
            continue

        if dry_run:
            result.sent += 1
            log(f"#{nomination.pk}: WOULD send to {email} ({name})")
            continue

        # Claim the row first so two overlapping runs can't both send it.
        with transaction.atomic():
            claimed = Nominations.objects.filter(
                pk=nomination.pk,
                confirmation_status__in=[Nominations.ConfirmationStatus.NOT_SENT, Nominations.ConfirmationStatus.FAILED],
            ).exclude(review_status=Nominations.ReviewStatus.REJECTED).update(
                confirmation_status=Nominations.ConfirmationStatus.SENT,
                confirmation_attempts=nomination.confirmation_attempts + 1,
            )
        if not claimed:
            continue  # rejected or handled meanwhile

        try:
            deliver(build_message(email, name, connection=connection))
        except Exception as exc:  # noqa: BLE001 - record any SMTP failure and retry next run
            _mark(nomination.pk, Nominations.ConfirmationStatus.FAILED, f"{type(exc).__name__}: {exc}")
            result.failed += 1
            logger.exception("Orbit confirmation failed for nomination %s", nomination.pk)
            log(f"#{nomination.pk}: FAILED ({exc})")
            continue

        _mark(nomination.pk, Nominations.ConfirmationStatus.SENT, f"Sent to {email}.", sent=True)
        result.sent += 1
        log(f"#{nomination.pk}: sent to {email}")

    return result
