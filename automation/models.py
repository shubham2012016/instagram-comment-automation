from django.db import models


class InstagramAccount(models.Model):
    ig_user_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=150, blank=True)
    access_token = models.TextField()
    token_expires_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"@{self.username}" if self.username else self.ig_user_id


class Product(models.Model):
    name = models.CharField(max_length=255)
    product_url = models.URLField(max_length=1000)
    reply_text = models.TextField(
        blank=True,
        default="Thanks for commenting! Here is the product link:"
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class InstagramPost(models.Model):
    account = models.ForeignKey(
        InstagramAccount,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    media_id = models.CharField(max_length=150, unique=True)
    caption = models.TextField(blank=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="instagram_posts",
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.media_id} → {self.product.name}"


class ProcessedComment(models.Model):
    comment_id = models.CharField(max_length=150, unique=True)
    account = models.ForeignKey(
        InstagramAccount,
        on_delete=models.CASCADE,
        related_name="processed_comments",
    )
    post = models.ForeignKey(
        InstagramPost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_comments",
    )
    commenter_id = models.CharField(max_length=150, blank=True)
    commenter_username = models.CharField(max_length=150, blank=True)
    text = models.TextField(blank=True)
    reply_message_id = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=30, default="received")
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    replied_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.comment_id} [{self.status}]"
