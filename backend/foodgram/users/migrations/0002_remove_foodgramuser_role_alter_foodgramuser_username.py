# Generated by Django 4.2.4 on 2023-09-09 22:14

import django.contrib.auth.validators
from django.db import migrations, models
import users.validators


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='foodgramuser',
            name='role',
        ),
        migrations.AlterField(
            model_name='foodgramuser',
            name='username',
            field=models.CharField(max_length=150, null=True, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator(), users.validators.validate_username], verbose_name='Никнейм'),
        ),
    ]
