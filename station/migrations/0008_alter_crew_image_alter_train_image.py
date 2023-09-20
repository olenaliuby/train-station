# Generated by Django 4.2.5 on 2023-09-20 19:33

from django.db import migrations, models
import station.upload_to_path


class Migration(migrations.Migration):

    dependencies = [
        ('station', '0007_alter_journey_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crew',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=station.upload_to_path.UploadToPath('crew-images/')),
        ),
        migrations.AlterField(
            model_name='train',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=station.upload_to_path.UploadToPath('train-images/')),
        ),
    ]