from django.contrib import admin
from .models import InstagramAccount, Product, InstagramPost, ProcessedComment


@admin.register(InstagramAccount)
class InstagramAccountAdmin(admin.ModelAdmin):
    list_display = ("ig_user_id", "username", "active", "token_expires_at", "updated_at")
    search_fields = ("ig_user_id", "username")
    list_filter = ("active",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "product_url", "active", "updated_at")
    search_fields = ("name", "product_url")
    list_filter = ("active",)


@admin.register(InstagramPost)
class InstagramPostAdmin(admin.ModelAdmin):
    list_display = ("media_id", "account", "product", "active", "updated_at")
    search_fields = ("media_id", "caption")
    list_filter = ("active", "account")
    autocomplete_fields = ("account", "product")


@admin.register(ProcessedComment)
class ProcessedCommentAdmin(admin.ModelAdmin):
    list_display = (
        "comment_id",
        "account",
        "post",
        "commenter_username",
        "status",
        "created_at",
        "replied_at",
    )
    search_fields = ("comment_id", "commenter_id", "commenter_username", "text")
    list_filter = ("status", "account")
    readonly_fields = (
        "comment_id",
        "account",
        "post",
        "commenter_id",
        "commenter_username",
        "text",
        "reply_message_id",
        "status",
        "error_message",
        "created_at",
        "replied_at",
    )
