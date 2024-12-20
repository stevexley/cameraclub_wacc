# Generated by Django 4.2.5 on 2024-10-26 02:29

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0033_alter_newsletter_issue_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsletter',
            name='issue_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 10, 26, 10, 29, 0, 789493)),
        ),
        migrations.AlterField(
            model_name='position',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='position', to='main.person'),
        ),
    ]
