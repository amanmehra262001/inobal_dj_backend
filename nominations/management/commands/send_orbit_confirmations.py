"""
Send the Orbit Edition "Official Selection Confirmation" emails that are due.

Run every hour from cron, e.g.:
    0 * * * * cd /path/to/inobal_dj_backend && /path/to/venv/bin/python manage.py send_orbit_confirmations >> /var/log/orbit_confirmations.log 2>&1

Options:
    --dry-run              list who would get the email, send nothing
    --limit N              send at most N in this run
    --test-to ADDRESS      send one sample email to ADDRESS (nothing else happens)
    --test-name "Name"     name used in the sample (default "Vijay Lagariya")
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from nominations import orbit_confirmation as oc


class Command(BaseCommand):
    help = "Send due Orbit Edition selection confirmation emails (skips rejected nominations)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--test-to", default=None)
        parser.add_argument("--test-name", default="Vijay Lagariya")

    def handle(self, *args, **opts):
        if opts["test_to"]:
            connection = None if oc.relay_ready() else oc.media_connection()
            msg = oc.build_message(opts["test_to"], opts["test_name"], connection=connection)
            try:
                oc.deliver(msg)
            except Exception as exc:  # noqa: BLE001
                raise CommandError(f"Sending the test email failed: {exc}") from exc
            self.stdout.write(self.style.SUCCESS(f"Test email sent to {opts['test_to']} via {'website relay' if oc.relay_ready() else 'SMTP'}: {msg.subject}"))
            return

        started = timezone.now()
        result = oc.send_due(dry_run=opts["dry_run"], limit=opts["limit"], log=self.stdout.write)
        label = "DRY RUN — " if opts["dry_run"] else ""
        self.stdout.write(
            f"{label}{started:%Y-%m-%d %H:%M} UTC: sent {result.sent}, skipped {result.skipped}, "
            f"failed {result.failed}, waiting for approval {result.waiting_for_review}"
        )
