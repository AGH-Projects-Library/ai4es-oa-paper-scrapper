from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0001_initial'),
    ]

    operations = [
        # Drop the placeholder Papers model created in 0001_initial.
        # papers_papers has no data so no data migration is needed.
        migrations.DeleteModel(name='Papers'),

        migrations.CreateModel(
            name='ResolvedPaper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doi', models.CharField(max_length=255, unique=True)),
                ('paper_id', models.CharField(blank=True, max_length=255)),
                ('title', models.CharField(max_length=512)),
                ('source', models.CharField(max_length=100)),
                ('authors', models.JSONField(default=list)),
                ('emails', models.JSONField(default=list)),
                ('extraction_method', models.CharField(blank=True, max_length=50)),
                ('md_path', models.CharField(blank=True, max_length=512)),
                ('html_path', models.CharField(blank=True, max_length=512)),
                ('pdf_path', models.CharField(blank=True, max_length=512)),
                ('processed_at', models.DateTimeField(auto_now_add=True)),
                ('rob_artifacts', models.JSONField(default=list)),
                ('available_sections', models.JSONField(default=list)),
            ],
        ),

        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section_id', models.CharField(max_length=512)),
                ('heading', models.CharField(max_length=512)),
                ('order', models.IntegerField(default=0)),
                ('md_path', models.CharField(blank=True, max_length=512)),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='papers.resolvedpaper')),
            ],
            options={
                'ordering': ['order'],
            },
        ),

        migrations.AddConstraint(
            model_name='section',
            constraint=models.UniqueConstraint(fields=('paper', 'section_id'), name='unique_paper_section_id'),
        ),
    ]
