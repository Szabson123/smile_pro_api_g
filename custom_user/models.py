from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class CentralUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class CentralUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    objects = CentralUserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email