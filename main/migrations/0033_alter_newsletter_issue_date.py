# Generated by Django 4.2.5 on 2024-10-19 09:26

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0032_alter_awardtype_options_alter_competition_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsletter',
            name='issue_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 10, 19, 17, 26, 36, 865640)),
        ),
    ]
