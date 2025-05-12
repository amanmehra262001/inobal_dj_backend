from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, unique_id, email=None, password=None, auth_type=None):
        if not unique_id:
            raise ValueError("Users must have a unique ID")

        user = self.model(
            unique_id=unique_id,
            email=email,
            auth_type=auth_type
        )
        
        if password:
            user.set_password(password)  # 🔥 Use set_password
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
        user.is_staff = True   # 🔥 Set is_staff
        user.is_active = True  # 🔥 Set is_active
        user.save(using=self._db)
        return user


class UserAuth(AbstractBaseUser):
    unique_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    auth_type = models.CharField(max_length=10, blank=True, null=True)  # 🔥 Store auth type (e.g., 'email', 'google')

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
    user = models.OneToOneField(
        UserAuth, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=255)
    image = models.CharField(max_length=255, blank=True, null=True)
    occupation = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'user_profile'
