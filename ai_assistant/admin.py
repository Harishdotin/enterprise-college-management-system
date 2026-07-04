from django.contrib import admin
from .models import AIConfiguration, AIChatMessage, AIAuditLog, AIDocument

@admin.register(AIConfiguration)
class AIConfigurationAdmin(admin.ModelAdmin):
    list_display = ('is_enabled', 'provider', 'model_name')

@admin.register(AIChatMessage)
class AIChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'timestamp')
    list_filter = ('role', 'timestamp')

@admin.register(AIAuditLog)
class AIAuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'intent', 'execution_time_ms', 'status', 'timestamp')
    list_filter = ('status', 'intent')


@admin.register(AIDocument)
class AIDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'document_type', 'tone', 'created_at', 'regeneration_count')
    list_filter = ('document_type', 'tone', 'created_at')
    search_fields = ('title', 'content', 'user__username')
