from django.db import models
from django.conf import settings

class AIConfiguration(models.Model):
    PROVIDER_CHOICES = [
        ('MOCK', 'Mock / Rule-Based Local Fallback (Default)'),
        ('GEMINI', 'Google Gemini AI Api'),
        ('OPENAI', 'OpenAI ChatGPT Api'),
    ]

    is_enabled = models.BooleanField(default=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='MOCK')
    api_key = models.CharField(max_length=255, blank=True, null=True)
    model_name = models.CharField(max_length=100, default='gemini-1.5-flash')
    temperature = models.DecimalField(max_digits=3, decimal_places=2, default=0.7)

    class Meta:
        verbose_name = "AI Configuration"
        verbose_name_plural = "AI Configurations"

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(id=1)
        return config

    def __str__(self):
        return f"AI Config - Enabled: {self.is_enabled} (Provider: {self.provider})"


class AIChatMessage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_chats'
    )
    role = models.CharField(max_length=15, choices=[('user', 'User'), ('assistant', 'Assistant')])
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.username} ({self.role}): {self.message[:30]}..."


class AIAuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ai_audit_logs'
    )
    query = models.TextField()
    intent = models.CharField(max_length=100, default='unknown')
    execution_time_ms = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[('SUCCESS', 'Success'), ('FALLBACK', 'Fallback'), ('ERROR', 'Error')])
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Audit: {self.user.username if self.user else 'System'} - Intent: {self.intent} ({self.status})"


class AIDocument(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_documents'
    )
    document_type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    content = models.TextField()
    tone = models.CharField(max_length=50, default='Formal')
    created_at = models.DateTimeField(auto_now_add=True)
    regeneration_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.document_type}) - {self.user.username}"
