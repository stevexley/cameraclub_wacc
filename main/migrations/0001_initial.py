# Generated by Django 4.2.5 on 2023-09-28 10:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Awarders',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('awarded_by', models.CharField(blank=True, max_length=100)),
                ('judge', models.BooleanField(default=False)),
                ('members', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Competition',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, null=True)),
                ('open_for_entries', models.DateTimeField()),
                ('entries_close', models.DateTimeField()),
                ('display_all', models.BooleanField(default=False)),
                ('display_awarded', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='CompetitionType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('type', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('starts', models.DateTimeField()),
                ('ends', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100)),
                ('print', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('rule', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('firstname', models.CharField(max_length=50)),
                ('surname', models.CharField(max_length=50)),
                ('mobile', models.CharField(max_length=50)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['surname', 'firstname'],
            },
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('joined', models.DateField(auto_now=True, null=True)),
                ('current', models.BooleanField()),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.person')),
            ],
        ),
        migrations.CreateModel(
            name='Judge',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('current', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.person')),
            ],
        ),
        migrations.CreateModel(
            name='ImageCompetitionComment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('comment', models.TextField(null=True)),
                ('competition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.competition')),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.image')),
            ],
        ),
        migrations.AddField(
            model_name='image',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='main.person'),
        ),
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('public_after', models.DateTimeField(null=True)),
                ('member_upload_from', models.DateTimeField(null=True)),
                ('member_upload_until', models.DateTimeField(null=True)),
                ('event', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='main.event')),
                ('images', models.ManyToManyField(to='main.image')),
            ],
        ),
        migrations.AddField(
            model_name='competition',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='main.event'),
        ),
        migrations.AddField(
            model_name='competition',
            name='images',
            field=models.ManyToManyField(to='main.image'),
        ),
        migrations.AddField(
            model_name='competition',
            name='rules',
            field=models.ManyToManyField(to='main.rule'),
        ),
        migrations.AddField(
            model_name='competition',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='main.competitiontype'),
        ),
        migrations.CreateModel(
            name='AwardType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=20)),
                ('points', models.SmallIntegerField(default=0)),
                ('display_award', models.BooleanField(default=True)),
                ('display_image', models.BooleanField(default=True)),
                ('active', models.BooleanField(default=True)),
                ('awarded_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='main.awarders')),
            ],
        ),
        migrations.CreateModel(
            name='Award',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('competition', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='main.competition')),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.image')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='main.awardtype')),
            ],
        ),
    ]
