# Generated by Django 4.2.13 on 2024-11-23 23:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('archivements', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='archivements',
            old_name='archivement_name',
            new_name='archivementName',
        ),
    ]