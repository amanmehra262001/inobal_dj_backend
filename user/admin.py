from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import UserAuth, UserProfile, AdminProfile


# Form for creating users in the admin
class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)
    is_staff = forms.BooleanField(label='Staff status', required=False, initial=False)

    class Meta:
        model = UserAuth
        fields = ('email', 'auth_type', 'is_staff')  # <-- added is_staff here

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# Form for updating users in the admin
class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = UserAuth
        fields = ('email', 'password', 'is_active', 'is_staff', 'is_superuser')

    def clean_password(self):
        return self.initial["password"]


# Inline for AdminProfile
class AdminProfileInline(admin.StackedInline):
    model = AdminProfile
    can_delete = False
    verbose_name_plural = 'Admin Profile'


# Custom UserAdmin
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    inlines = [AdminProfileInline]

    list_display = ('unique_id', 'email', 'is_staff', 'is_superuser', 'auth_type', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    fieldsets = (
        (None, {'fields': ('email', 'password', 'auth_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ['last_login']}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'auth_type', 'password1', 'password2')}
        ),
    )
    search_fields = ('email', 'unique_id')
    ordering = ('email',)
    filter_horizontal = ()  # ✅ Remove 'groups' and 'user_permissions'


# Register models
admin.site.register(UserAuth, UserAdmin)
admin.site.register(UserProfile)
admin.site.register(AdminProfile)
