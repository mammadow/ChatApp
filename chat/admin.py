from django.contrib import admin
from chat.models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("user", "content", "created_at")
    list_filter = ("created_at", "user")
    search_fields = ("user__username", "content")
    ordering = ("-created_at",)
