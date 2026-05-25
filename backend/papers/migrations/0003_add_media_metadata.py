from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0002_replace_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='resolvedpaper',
            name='tables_metadata',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='resolvedpaper',
            name='images_metadata',
            field=models.JSONField(default=list),
        ),
    ]
