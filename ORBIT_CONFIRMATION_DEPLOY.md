# Orbit Edition — Official Selection Confirmation email (deploy notes)

What this adds
- `Nominations` gets an editorial review status (Pending / Approved / Rejected) and confirmation-email tracking
  (`confirmation_status`, `confirmation_sent_at`, `confirmation_attempts`, `confirmation_note`).
- Django admin (`/admin/nominations/nominations/`): name, email, review status editable in the list,
  bulk actions "Reject selected (no confirmation email)", "Approve selected", "Mark selected as pending review".
- API for the admin panel: `PATCH /api/nominations/admin/submissions/<id>/` with `{"review_status": "rejected" | "approved" | "pending"}`
  (same JWT + staff auth as the GET). The GET responses now include the new fields.
- `python manage.py send_orbit_confirmations` sends the email from media@worthminds.com to every nomination of form 2
  that is older than 36 h, not rejected (or, in approve mode, approved), submitted after the go-live date, and not sent yet.
  One email per address; SMTP failures are retried on the next run (max 3 attempts).

## 1. Deploy the code
    git pull
    pip install -r requirements.txt          # no new packages
    python manage.py makemigrations nominations   # migrations are git-ignored in this repo, so create it on the server
    python manage.py migrate
    # restart gunicorn / the app service

Existing nominations get review_status = pending and confirmation_status = not_sent. They are NOT emailed
because only nominations submitted on/after ORBIT_CONFIRMATION_START are considered.

## 2. Environment variables (.env on the server)
    MEDIA_EMAIL_USER=media@worthminds.com
    MEDIA_EMAIL_PASSWORD=<Google App Password of media@worthminds.com>
    ORBIT_CONFIRMATION_START=2026-11-01          # go-live date (IST); nominations before this are never emailed
    # optional (defaults shown)
    ORBIT_CONFIRMATION_DELAY_HOURS=36
    ORBIT_CONFIRMATION_MODE=auto                 # auto = everyone not rejected; approve = only Approved ones
    ORBIT_CONFIRMATION_DESIGN=letter             # letter | night | certificate
    ORBIT_CONFIRMATION_STAMP=mono                # mono (grey) | color
    ORBIT_CONFIRMATION_BCC=                      # e.g. admin@worthminds.com to receive a copy of each
    ORBIT_CONFIRMATION_FORM_ID=2
    MEDIA_EMAIL_HOST=smtp.gmail.com
    MEDIA_EMAIL_PORT=465

Security (strongly recommended, this repository is public):
    DJANGO_SECRET_KEY=<new random 50+ chars>
    JWT_SIGNING_SECRET_KEY=<new random 50+ chars>   # everyone must log in to the admin panel again afterwards
    DJANGO_DEBUG=False                              # make sure /static is served by nginx first

## 3. Test before switching on
    python manage.py send_orbit_confirmations --test-to you@example.com --test-name "Your Name"
    python manage.py send_orbit_confirmations --dry-run

## 4. Cron (hourly)
    0 * * * * cd /path/to/inobal_dj_backend && /path/to/venv/bin/python manage.py send_orbit_confirmations >> /var/log/orbit_confirmations.log 2>&1

The images used by the email are served from https://www.worthminds.com/images/email/ (website repo).
