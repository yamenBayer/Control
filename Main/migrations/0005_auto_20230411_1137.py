# Generated by Django 3.2.12 on 2023-04-11 11:37

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Main', '0004_auto_20230329_1443'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='about',
            field=models.TextField(default=''),
        ),
        migrations.CreateModel(
            name='statistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_id', models.IntegerField(default=-1)),
                ('project_id', models.IntegerField(default=-1)),
                ('task_or_project', models.BooleanField(default=False)),
                ('done_or_outdated', models.BooleanField(default=False)),
                ('date', models.DateField(default=datetime.datetime.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='User_Statistics', to='Main.profile')),
            ],
        ),
    ]
