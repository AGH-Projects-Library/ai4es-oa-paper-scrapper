from django.db import models

# Create your models here.

class ResolvedPaper(models.Model):
    doi = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    authors = models.CharField(max_length=255)
    source = models.CharField(max_length=100)
    year = models.IntegerField()
    availableSections = models.JSONField(default=list, blank=True)


class Section(models.Model):

    paper = models.ForeignKey(ResolvedPaper, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.IntegerField(default=0)


