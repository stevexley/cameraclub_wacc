# Generated by Django 4.2.5 on 2023-10-22 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_position'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='position',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='position',
            name='order',
            field=models.SmallIntegerField(default=1),
            preserve_default=False,
        ),
    ]
