# Generated by Django 4.2.5 on 2023-10-18 13:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_competition_rules_alter_competition_images'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='competition',
            name='rules',
        ),
    ]
