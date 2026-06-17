from django.db import models
from users_app.models import User

PROJECT_TYPE = [
    ('solo', 'Solo'),
    ('team', 'Team'),
]

class ProjectManager(models.Manager):
    def project_validator(self, postData):
        errors = {}
        if len(postData.get('title', '').strip()) < 2:
            errors['title'] = "Title must be at least 2 characters."
        if len(postData.get('description', '').strip()) < 10:
            errors['description'] = "Description must be at least 10 characters."
        if len(postData.get('tech_stack', '').strip()) < 2:
            errors['tech_stack'] = "Tech stack is required (comma separated)."
        if not postData.get('project_type'):
            errors['project_type'] = "Please select a project type."
        return errors


class Project(models.Model):
    title        = models.CharField(max_length=255)
    description  = models.TextField()
    tech_stack   = models.CharField(max_length=255)
    github_url   = models.CharField(max_length=255, blank=True, default='')
    image        = models.ImageField(upload_to='projects/', blank=True, null=True)
    project_type = models.CharField(max_length=10, choices=PROJECT_TYPE, default='solo')
    share_count  = models.IntegerField(default=0)
    owner        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    objects      = ProjectManager()

    @property
    def tech_list(self):
        return [t.strip() for t in self.tech_stack.split(',') if t.strip()]

    def __str__(self):
        return self.title


class Contributor(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='contributors')
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contributions')
    role    = models.CharField(max_length=120, blank=True, default='')

    class Meta:
        unique_together = ('project', 'user')


class Comment(models.Model):
    content    = models.TextField()
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    project    = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class Like(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    project    = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')


class Share(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares')
    project    = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='shares')
    created_at = models.DateTimeField(auto_now_add=True)