from django.db import models
from django.utils.translation import gettext_lazy as _


class NominationForm(models.Model):
    """
    Stores the dynamic definition for a nomination form.

    The actual fields are defined by related `NominationFormField` rows,
    so the admin can add/edit field keys, labels, types, and options.
    """

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Nomination Form")
        verbose_name_plural = _("Nomination Forms")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class NominationFormField(models.Model):
    class FieldType(models.TextChoices):
        TEXT = "text", _("Text")
        TEXTAREA = "textarea", _("Textarea")
        EMAIL = "email", _("Email")
        URL = "url", _("URL")
        NUMBER = "number", _("Number")
        INTEGER = "integer", _("Integer")
        BOOLEAN = "boolean", _("Boolean")
        DATE = "date", _("Date")
        DATETIME = "datetime", _("Datetime")
        SINGLE_CHOICE = "single_choice", _("Single choice")
        MULTI_CHOICE = "multi_choice", _("Multi choice")

    form = models.ForeignKey(
        NominationForm,
        on_delete=models.CASCADE,
        related_name="fields",
    )

    # Key used to store the response value inside `Nominations.responses`
    # as JSON key/value pairs.
    key = models.SlugField(
        max_length=100,
        help_text=_("JSON key for this field (must be unique per form)."),
    )
    label = models.CharField(max_length=255)

    field_type = models.CharField(
        max_length=30,
        choices=FieldType.choices,
        default=FieldType.TEXT,
    )
    required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    help_text = models.TextField(blank=True, default="")

    # For choice fields, store available options.
    # Expected flexible formats, for example:
    # - ["Option A", "Option B"]
    # - [{"value": "a", "label": "Option A"}, ...]
    options = models.JSONField(blank=True, default=list)

    class Meta:
        verbose_name = _("Nomination Form Field")
        verbose_name_plural = _("Nomination Form Fields")
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["form", "key"],
                name="unique_nomination_form_field_key_per_form",
            )
        ]

    def __str__(self) -> str:
        return f"{self.form.name}: {self.key}"


class Nominations(models.Model):
    """
    Stores each user submission for a given `NominationForm`.

    Since the form fields are dynamic, user responses are stored as JSON
    key/value pairs inside `responses`.
    """

    form = models.ForeignKey(
        NominationForm,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    responses = models.JSONField(blank=True, default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Nomination Submission")
        verbose_name_plural = _("Nomination Submissions")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.form.name} - {self.id}"
 