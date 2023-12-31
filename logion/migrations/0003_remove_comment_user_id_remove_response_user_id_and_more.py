# Generated by Django 4.2.4 on 2023-09-05 02:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logion', '0002_remove_customuser_test'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='user_id',
        ),
        migrations.RemoveField(
            model_name='response',
            name='user_id',
        ),
        migrations.RemoveField(
            model_name='suggestion',
            name='submitter_user_id',
        ),
        migrations.AddField(
            model_name='comment',
            name='commenter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='response',
            name='commenter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='suggestion',
            name='submitter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
