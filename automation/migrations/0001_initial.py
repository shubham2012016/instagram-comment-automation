from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="InstagramAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ig_user_id", models.CharField(max_length=100, unique=True)),
                ("username", models.CharField(blank=True, max_length=150)),
                ("access_token", models.TextField()),
                ("token_expires_at", models.DateTimeField(blank=True, null=True)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("product_url", models.URLField(max_length=1000)),
                ("reply_text", models.TextField(blank=True, default="Thanks for commenting! Here is the product link:")),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="InstagramPost",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("media_id", models.CharField(max_length=150, unique=True)),
                ("caption", models.TextField(blank=True)),
                ("active", models.BooleanField(default=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="posts", to="automation.instagramaccount")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="instagram_posts", to="automation.product")),
            ],
        ),
        migrations.CreateModel(
            name="ProcessedComment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("comment_id", models.CharField(max_length=150, unique=True)),
                ("commenter_id", models.CharField(blank=True, max_length=150)),
                ("commenter_username", models.CharField(blank=True, max_length=150)),
                ("text", models.TextField(blank=True)),
                ("reply_message_id", models.CharField(blank=True, max_length=300)),
                ("status", models.CharField(default="received", max_length=30)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("replied_at", models.DateTimeField(blank=True, null=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="processed_comments", to="automation.instagramaccount")),
                ("post", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="processed_comments", to="automation.instagrampost")),
            ],
        ),
    ]
