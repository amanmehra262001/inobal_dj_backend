from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from common.constants import S3_BLOG_BUCKET_NAME
from common.utils.s3_utils import upload_image_to_s3
from common.views import CustomJWTAuthentication, IsAdminUser
from .models import NominationForm, NominationFormField, Nominations
from .serializers import (
    NominationFormSerializer,
    NominationsSerializer,
    NominationSubmitSerializer,
)


class NominationFormAdminListCreateView(APIView):
    """
    Admin: list all nomination forms (including inactive) and create with optional nested fields.
    """

    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        forms = NominationForm.objects.prefetch_related("fields").order_by("-created_at")
        serializer = NominationFormSerializer(forms, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = NominationFormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NominationFormAdminDetailView(APIView):
    """
    Admin: retrieve, full update, partial update, or delete a nomination form.
    When `fields` is sent on PUT/PATCH, existing fields are replaced by the payload.
    """

    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        return get_object_or_404(
            NominationForm.objects.prefetch_related("fields"), pk=pk
        )

    def get(self, request, pk):
        form = self.get_object(pk)
        return Response(NominationFormSerializer(form).data)

    def put(self, request, pk):
        form = self.get_object(pk)
        serializer = NominationFormSerializer(form, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        form = self.get_object(pk)
        serializer = NominationFormSerializer(form, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        form = self.get_object(pk)
        form.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicNominationFormListView(APIView):
    """Anyone: list active nomination forms (summary, no heavy nesting)."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        forms = NominationForm.objects.filter(is_active=True).order_by("-created_at")
        data = [
            {
                "id": f.id,
                "name": f.name,
                "description": f.description,
            }
            for f in forms
        ]
        return Response(data)


class PublicNominationFormDetailView(APIView):
    """Anyone: get one active form with all field definitions for rendering the UI."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, pk):
        form = get_object_or_404(
            NominationForm.objects.prefetch_related("fields"),
            pk=pk,
            is_active=True,
        )
        return Response(NominationFormSerializer(form).data)


class NominationSubmitView(APIView):
    """Anyone: submit responses for an active form."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, pk):
        form = get_object_or_404(
            NominationForm.objects.prefetch_related("fields"),
            pk=pk,
            is_active=True,
        )
        submit_serializer = NominationSubmitSerializer(
            data=request.data,
            context={"form": form},
        )
        if not submit_serializer.is_valid():
            return Response(submit_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        nomination = Nominations.objects.create(
            form=form,
            responses=submit_serializer.validated_data["responses"],
        )
        return Response(
            NominationsSerializer(nomination).data,
            status=status.HTTP_201_CREATED,
        )


class NominationsAdminListView(APIView):
    """Admin: list all submissions; optional ?form=<id> to filter by form."""

    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = Nominations.objects.select_related("form").order_by("-created_at")
        form_id = request.query_params.get("form")
        if form_id is not None:
            try:
                qs = qs.filter(form_id=int(form_id))
            except (TypeError, ValueError):
                return Response(
                    {"form": "Invalid form id."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        serializer = NominationsSerializer(qs, many=True)
        return Response(serializer.data)


class NominationsAdminDetailView(APIView):
    """Admin: retrieve a single submission."""

    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        nomination = get_object_or_404(
            Nominations.objects.select_related("form"), pk=pk
        )
        return Response(NominationsSerializer(nomination).data)


class NominationFieldTypeListView(APIView):
    """Anyone: list all available nomination field types."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        field_types = [
            {"value": value, "label": label}
            for value, label in NominationFormField.FieldType.choices
        ]
        return Response(field_types)


class NominationFieldFileUploadView(APIView):
    """
    Anyone: upload image/pdf for a configured file field.
    Returns uploaded file metadata (key/url) that can be saved in responses JSON.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request, form_id, field_key):
        form = get_object_or_404(
            NominationForm.objects.prefetch_related("fields"),
            pk=form_id,
            is_active=True,
        )
        field = get_object_or_404(form.fields, key=field_key)

        if field.field_type != NominationFormField.FieldType.FILE:
            return Response(
                {"error": "This field is not configured as file type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        files = request.FILES.getlist("file")
        if not files:
            files = request.FILES.getlist("files")
        if not files:
            return Response(
                {"error": "No files provided. Use multipart key `file` or `files`."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not field.allow_multiple_files and len(files) > 1:
            return Response(
                {"error": "Only one file is allowed for this field."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if field.max_files and len(files) > field.max_files:
            return Response(
                {"error": f"Maximum number of files allowed is {field.max_files}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        size_limit_bytes = None
        if field.max_file_size_mb:
            size_limit_bytes = field.max_file_size_mb * 1024 * 1024

        folder = request.data.get("folder", f"nominations/{form.id}/{field.key}")
        uploaded_files = []
        for upload_file in files:
            if upload_file.content_type not in ("application/pdf",) and not (
                upload_file.content_type or ""
            ).startswith("image/"):
                return Response(
                    {
                        "error": (
                            f"Unsupported file type `{upload_file.content_type}`. "
                            "Only images and PDFs are allowed."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if size_limit_bytes and upload_file.size > size_limit_bytes:
                return Response(
                    {
                        "error": (
                            f"File `{upload_file.name}` exceeds size limit of "
                            f"{field.max_file_size_mb} MB."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            upload_response = upload_image_to_s3(
                image_file=upload_file,
                folder=folder,
                bucket=S3_BLOG_BUCKET_NAME,
            )
            if upload_response["error"]:
                return Response(
                    {"error": upload_response["message"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            uploaded_files.append(
                {
                    "name": upload_file.name,
                    "content_type": upload_file.content_type,
                    "size": upload_file.size,
                    "key": upload_response["key"],
                    "url": upload_response["url"],
                }
            )

        if field.allow_multiple_files:
            return Response({"files": uploaded_files}, status=status.HTTP_201_CREATED)

        return Response({"file": uploaded_files[0]}, status=status.HTTP_201_CREATED)


    def delete(self, request, form_id, field_key):
        form = get_object_or_404(
            NominationForm.objects.prefetch_related("fields"),
            pk=form_id,
            is_active=True,
        )
        field = get_object_or_404(form.fields, key=field_key)

        if field.field_type != NominationFormField.FieldType.FILE:
            return Response(
                {"error": "This field is not configured as file type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        key = request.data.get("key")
        if not key:
            return Response(
                {"error": "S3 object `key` is required in the request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Guard: only allow deletion of keys scoped to this form + field
        expected_prefix = f"nominations/{form_id}/{field_key}/"
        if not key.startswith(expected_prefix):
            return Response(
                {"error": "Key does not belong to this form field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = delete_file_from_s3(key=key, bucket=S3_BLOG_BUCKET_NAME)
        if result["error"]:
            return Response(
                {"error": result["message"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)