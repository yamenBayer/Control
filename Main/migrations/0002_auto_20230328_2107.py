# Generated by Django 3.2.12 on 2023-03-28 21:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Main', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productphoto',
            name='photo',
            field=models.ImageField(default='Control/static/products-images/default/product.png', upload_to='Control/static/products-images/%y/%m/%d/'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='photo',
            field=models.ImageField(default='Control/static/cover-images/default/Login.png', upload_to='Control/static/cover-images/%y/%m/%d/'),
        ),
        migrations.AlterField(
            model_name='team',
            name='photo',
            field=models.ImageField(default='Control/static/team-images/default/defaultTeam.jpg', upload_to='Control/static/team-images/%y/%m/%d/'),
        ),
    ]