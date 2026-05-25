from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0003_add_media_metadata'),
    ]

    operations = [
        # Replace the JSONField denormalisations with proper relational models.
        migrations.RemoveField(
            model_name='resolvedpaper',
            name='tables_metadata',
        ),
        migrations.RemoveField(
            model_name='resolvedpaper',
            name='images_metadata',
        ),

        migrations.AddField(
            model_name='resolvedpaper',
            name='export_json_path',
            field=models.CharField(blank=True, default='', max_length=512),
            preserve_default=False,
        ),

        migrations.CreateModel(
            name='Table',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('table_index', models.IntegerField()),
                ('global_index', models.IntegerField()),
                ('csv_path', models.CharField(blank=True, max_length=512)),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tables', to='papers.resolvedpaper')),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tables', to='papers.section')),
            ],
            options={
                'ordering': ['global_index'],
            },
        ),

        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idx', models.IntegerField()),
                ('placeholder', models.CharField(blank=True, max_length=255)),
                ('caption', models.TextField(blank=True)),
                ('path', models.CharField(blank=True, max_length=512)),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='papers.resolvedpaper')),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='papers.section')),
            ],
            options={
                'ordering': ['idx'],
            },
        ),
    ]
