from rest_framework import serializers

from .models import NominationForm, NominationFormField, Nominations


class NominationFormFieldSerializer(serializers.ModelSerializer):
    label = serializers.CharField(allow_blank=True)

    class Meta:
        model = NominationFormField
        fields = (
            "id",
            "key",
            "label",
            "field_type",
            "required",
            "order",
            "space_occupancy",
            "help_text",
            "max_text_length",
            "options",
            "allow_multiple_files",
            "max_files",
            "max_file_size_mb",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        field_type = attrs.get("field_type", "")
        label = attrs.get("label", "")
        if field_type != NominationFormField.FieldType.SECTION_NOTE and not label.strip():
            raise serializers.ValidationError({"label": "This field may not be blank."})
        return attrs

class NominationFormSerializer(serializers.ModelSerializer):
    fields = NominationFormFieldSerializer(many=True, required=False)

    class Meta:
        model = NominationForm
        fields = (
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
            "fields",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        fields_data = validated_data.pop("fields", [])
        form = NominationForm.objects.create(**validated_data)
        for fd in fields_data:
            NominationFormField.objects.create(form=form, **fd)
        return form

    def update(self, instance, validated_data):
        fields_data = validated_data.pop("fields", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if fields_data is not None:
            instance.fields.all().delete()
            for fd in fields_data:
                NominationFormField.objects.create(form=instance, **fd)
        return instance


class NominationsSerializer(serializers.ModelSerializer):
    form_name = serializers.CharField(source="form.name", read_only=True)

    class Meta:
        model = Nominations
        fields = (
            "id",
            "form",
            "form_name",
            "responses",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "form_name", "created_at", "updated_at")


class NominationSubmitSerializer(serializers.Serializer):
    responses = serializers.JSONField(required=True)

    def validate(self, attrs):
        form: NominationForm = self.context["form"]
        responses = attrs.get("responses") or {}
        if not isinstance(responses, dict):
            raise serializers.ValidationError(
                {"responses": "Must be a JSON object (key/value pairs)."}
            )

        errors = {}
        for field in form.fields.all():
            # Section titles and notes are display-only — they hold no user
            # response and must never be validated or required on submit.
            if field.field_type in NominationFormField.DISPLAY_ONLY_TYPES:
                continue

            value = responses.get(field.key)
            if field.required and value in (None, "", []):
                errors[field.key] = "This field is required."
                continue

            if value in (None, "", []):
                continue

            if field.field_type in {
                NominationFormField.FieldType.TEXT,
                NominationFormField.FieldType.TEXTAREA,
                NominationFormField.FieldType.EMAIL,
                NominationFormField.FieldType.URL,
            }:
                text_value = str(value)
                if field.max_text_length and len(text_value) > field.max_text_length:
                    errors[field.key] = (
                        f"Maximum length is {field.max_text_length} characters."
                    )

            if field.field_type == NominationFormField.FieldType.FILE:
                files = value if isinstance(value, list) else [value]
                if not field.allow_multiple_files and len(files) > 1:
                    errors[field.key] = "Only one file is allowed for this field."
                    continue
                if field.max_files and len(files) > field.max_files:
                    errors[field.key] = (
                        f"Maximum number of files allowed is {field.max_files}."
                    )
                    continue

                for file_item in files:
                    if not isinstance(file_item, dict):
                        errors[field.key] = "Each uploaded file must be an object."
                        break
                    if not file_item.get("key") or not file_item.get("url"):
                        errors[field.key] = (
                            "Each uploaded file must include `key` and `url`."
                        )
                        break

        if errors:
            raise serializers.ValidationError(errors)

        return attrs