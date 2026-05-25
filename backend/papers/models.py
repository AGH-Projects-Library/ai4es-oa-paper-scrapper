from django.db import models


class ResolvedPaper(models.Model):
    doi = models.CharField(max_length=255, unique=True)
    paper_id = models.CharField(max_length=255, blank=True)   # pmcid or arxiv_id
    title = models.CharField(max_length=512)
    source = models.CharField(max_length=100)                 # 'pmc' | 'arxiv'
    authors = models.JSONField(default=list)
    emails = models.JSONField(default=list)
    extraction_method = models.CharField(max_length=50, blank=True)
    md_path = models.CharField(max_length=512, blank=True)
    html_path = models.CharField(max_length=512, blank=True)
    pdf_path = models.CharField(max_length=512, blank=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    rob_artifacts = models.JSONField(default=list)
    # [{"id": "methods", "name": "Methods"}, ...]
    available_sections = models.JSONField(default=list)
    # [{"global_index": 0, "section_id": "methods", "section_name": "Methods", "table_index": 0, "csv_path": "..."}, ...]
    tables_metadata = models.JSONField(default=list)
    # [{"idx": 0, "section_id": "methods", "section_name": "Methods", "placeholder": "FIG_1", "caption": "...", "path": "..."}, ...]
    images_metadata = models.JSONField(default=list)


class Section(models.Model):
    paper = models.ForeignKey(ResolvedPaper, on_delete=models.CASCADE, related_name='sections')
    section_id = models.CharField(max_length=512)   # slugified heading, e.g. "methods"
    heading = models.CharField(max_length=512)       # original heading text
    order = models.IntegerField(default=0)
    md_path = models.CharField(max_length=512, blank=True)

    class Meta:
        ordering = ['order']
        unique_together = [('paper', 'section_id')]
