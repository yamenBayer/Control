# Generated by Django 3.2.12 on 2023-03-28 21:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Main', '0002_auto_20230328_2107'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productphoto',
            name='photo',
            field=models.ImageField(default='static/products-images/default/product.png', upload_to='static/products-images/%y/%m/%d/'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='photo',
            field=models.ImageField(default='static/cover-images/default/Login.png', upload_to='static/cover-images/%y/%m/%d/'),
        ),
        migrations.AlterField(
            model_name='team',
            name='photo',
            field=models.ImageField(default='static/team-images/default/defaultTeam.jpg', upload_to='static/team-images/%y/%m/%d/'),
        ),
    ]
