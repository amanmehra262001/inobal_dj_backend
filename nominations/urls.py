from django.urls import path

from .views import (
    NominationFieldFileUploadView,
    NominationFieldTypeListView,
    NominationFormAdminDetailView,
    NominationFormAdminListCreateView,
    NominationsAdminDetailView,
    NominationsAdminListView,
    NominationSubmitView,
    PublicNominationFormDetailView,
    PublicNominationFormListView,
)

urlpatterns = [
    path("field-types/", NominationFieldTypeListView.as_view(), name="nomination-field-types"),
    path(
        "forms/<int:form_id>/fields/<slug:field_key>/upload/",
        NominationFieldFileUploadView.as_view(),
        name="nomination-field-file-upload",
    ),
    # Admin (JWT + staff)
    path("admin/forms/", NominationFormAdminListCreateView.as_view(), name="nomination-form-admin-list-create"),
    path("admin/forms/<int:pk>/", NominationFormAdminDetailView.as_view(), name="nomination-form-admin-detail"),
    path("admin/submissions/", NominationsAdminListView.as_view(), name="nomination-submissions-admin-list"),
    path("admin/submissions/<int:pk>/", NominationsAdminDetailView.as_view(), name="nomination-submissions-admin-detail"),
    # Public
    path("forms/", PublicNominationFormListView.as_view(), name="nomination-form-public-list"),
    path("forms/<int:pk>/", PublicNominationFormDetailView.as_view(), name="nomination-form-public-detail"),
    path("forms/<int:pk>/submit/", NominationSubmitView.as_view(), name="nomination-form-submit"),
]
