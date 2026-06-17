from django.db import models
import re
import bcrypt

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

class UserManager(models.Manager):

    def register_validator(self, postData):
        errors = {}
        full_name = postData.get('full_name', '').strip()
        if len(full_name) < 3 or ' ' not in full_name:
            errors['full_name'] = "Please enter your full name (first and last)."

        if not EMAIL_REGEX.match(postData.get('email', '')):
            errors['email'] = "Please enter a valid email address."
        elif User.objects.filter(email=postData.get('email')).exists():
            errors['email'] = "This email is already registered."

        if len(postData.get('password', '')) < 8:
            errors['password'] = "Password must be at least 8 characters."

        github = postData.get('github_url', '').strip()
        if github and 'github.com' not in github:
            errors['github_url'] = "Please enter a valid GitHub URL."

        return errors

    def login_validator(self, postData):
        errors = {}
        user = User.objects.filter(email=postData.get('email', '')).first()
        if not user:
            errors['email'] = "Invalid email or password."
        else:
            if not bcrypt.checkpw(postData['password'].encode(), user.password.encode()):
                errors['email'] = "Invalid email or password."
        return errors


class User(models.Model):
    full_name   = models.CharField(max_length=255)
    handle      = models.CharField(max_length=50, unique=True, blank=True)
    email       = models.EmailField(max_length=255, unique=True)
    password    = models.CharField(max_length=255)
    bio         = models.TextField(blank=True, default='')
    role_title  = models.CharField(max_length=120, blank=True, default='')
    github_url  = models.CharField(max_length=255, blank=True, default='')
    location    = models.CharField(max_length=120, blank=True, default='')
    avatar      = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    objects     = UserManager()

    def save(self, *args, **kwargs):
        if not self.handle:
            base = re.sub(r'[^a-zA-Z0-9]', '', self.full_name.split(' ')[0]).lower()
            candidate = base
            i = 1
            while User.objects.filter(handle=candidate).exclude(id=self.id).exists():
                candidate = f"{base}{i}"
                i += 1
            self.handle = candidate
        super().save(*args, **kwargs)

    @property
    def initials(self):
        parts = self.full_name.split(' ')
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return self.full_name[:2].upper()

    @property
    def first_name(self):
        return self.full_name.split(' ')[0]

    def __str__(self):
        return f"@{self.handle}"


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class UserSkill(models.Model):
    user  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='users')

    class Meta:
        unique_together = ('user', 'skill')


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')