from django.contrib import admin, messages
from django.utils import timezone

from .models import Nominations, NominationForm, NominationFormField


class NominationFormFieldInline(admin.TabularInline):
    model = NominationFormField
    extra = 1
    fields = (
        "order",
        "key",
        "label",
        "field_type",
        "required",
        "space_occupancy",
        "options",
        "help_text",
    )
    show_change_link = True


@admin.register(NominationForm)
class NominationFormAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")
    inlines = [NominationFormFieldInline]


@admin.register(Nominations)
class NominationsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nominee",
        "email",
        "form",
        "created_at",
        "review_status",
        "confirmation_status",
        "confirmation_sent_at",
    )
    list_display_links = ("id", "nominee")
    list_editable = ("review_status",)
    list_filter = ("form", "review_status", "confirmation_status")
    search_fields = ("id",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "reviewed_at",
        "confirmation_status",
        "confirmation_sent_at",
        "confirmation_attempts",
        "confirmation_note",
    )
    actions = ("reject_selected", "approve_selected", "mark_pending")

    @admin.display(description="Name")
    def nominee(self, obj):
        return obj.nominee_name or "—"

    @admin.display(description="Email")
    def email(self, obj):
        return obj.nominee_email or "—"

    def save_model(self, request, obj, form, change):
        if change and "review_status" in form.changed_data:
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)

    def _set_review(self, request, queryset, value, label):
        count = queryset.update(review_status=value, reviewed_at=timezone.now())
        self.message_user(request, f"{count} nomination(s) marked {label}.", messages.SUCCESS)

    @admin.action(description="Reject selected (no confirmation email)")
    def reject_selected(self, request, queryset):
        self._set_review(request, queryset, Nominations.ReviewStatus.REJECTED, "Rejected")

    @admin.action(description="Approve selected")
    def approve_selected(self, request, queryset):
        self._set_review(request, queryset, Nominations.ReviewStatus.APPROVED, "Approved")

    @admin.action(description="Mark selected as pending review")
    def mark_pending(self, request, queryset):
        self._set_review(request, queryset, Nominations.ReviewStatus.PENDING, "Pending review")
