# Generated by Django 5.0.6 on 2024-06-25 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DataTigHub",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
            options={
                "permissions": (("admin", "Admin - All admin tasks on this server"),),
                "managed": False,
                "default_permissions": (),
            },
        ),
    ]
