from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import uuid


class CustomUserManager(BaseUserManager):
    def create_user(self, unique_id, email=None, password=None, auth_type=None, is_subscriber=False):
        if not unique_id:
            raise ValueError("Users must have a unique ID")

        user = self.model(
            unique_id=unique_id,
            email=email,
            auth_type=auth_type,
            is_subscriber=is_subscriber
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, unique_id, email=None, password=None, auth_type=None):
        user = self.create_user(
            unique_id=unique_id,
            email=email,
            password=password,
            auth_type=auth_type
        )
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save(using=self._db)
        return user


class UserAuth(AbstractBaseUser):
    unique_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_subscriber = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    auth_type = models.CharField(max_length=10, blank=True, null=True)  # e.g., 'email', 'google'

    objects = CustomUserManager()

    USERNAME_FIELD = 'unique_id'

    def save(self, *args, **kwargs):
        if not self.unique_id:
            if self.email:
                self.unique_id = f"email_{uuid.uuid4().hex[:8]}"
            else:
                self.unique_id = uuid.uuid4().hex
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'user_auth'

    def __str__(self):
        return self.unique_id


class UserProfile(models.Model):
    user = models.OneToOneField(UserAuth, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=255)
    image_url = models.URLField(blank=True, null=True)
    image_key = models.CharField(max_length=255, blank=True, null=True)
    occupation = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'user_profile'


class AdminProfile(models.Model):
    user = models.OneToOneField(UserAuth, on_delete=models.CASCADE, related_name='admin_profile')
    full_name = models.CharField(max_length=255)
    # role = models.CharField(max_length=100, choices=[
    #     ('editor', 'Editor'),
    #     ('moderator', 'Moderator'),
    #     ('admin', 'Administrator'),
    # ])
    # department = models.CharField(max_length=100, blank=True, null=True)
    joined_on = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'admin_profile'

    def __str__(self):
        return f"{self.full_name}"


class SubscriberProfile(models.Model):
    user = models.OneToOneField(UserAuth, on_delete=models.CASCADE, related_name='subscriber_profile')
    full_name = models.CharField(max_length=255)
    subscription_plan = models.CharField(max_length=100, blank=True, null=True)
    subscription_start = models.DateField(null=True, blank=True)
    subscription_end = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'subscriber_profile'

    def __str__(self):
        return f"Subscriber: {self.full_name}"


class OmnisendContacts(models.Model):
    email = models.EmailField(unique=True, blank=True, null=True)
    omnisend_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="ID returned from Omnisend API"
    )
    is_contacted = models.BooleanField(default=False)
    is_subscribed = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Omnisend Contact"
        verbose_name_plural = "Omnisend Contacts"

    def __str__(self):
        return self.email or f"Contact {self.omnisend_id}"