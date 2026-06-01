"""
Management command: populate the DB from paper IDs inferred from backend/data/html/.

Usage:
    python manage.py load_from_data
    python manage.py load_from_data --dry-run

Each HTML file in data/html/ maps to one paper:
  - Files like  2205.14135.html  are treated as arXiv IDs.
  - Files like  PMC9373683.html  are treated as PMC IDs.

The command calls the same service that the API uses, so results are identical
to processing each DOI through the UI.  Images and PDFs that are already on
disk are reused; only HTML is always re-fetched.
"""
import os
import re

from django.conf import settings
from django.core.management.base import BaseCommand

from papers.services.resolve_doi import resolve_doi_to_paper


ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
PMC_RE   = re.compile(r"^PMC\d+$", re.IGNORECASE)


class Command(BaseCommand):
    help = "Populate DB from paper IDs found in backend/data/html/"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print which papers would be processed without actually processing them.",
        )

    def handle(self, *args, **options):
        dry_run   = options["dry_run"]
        html_dir  = os.path.join(str(settings.SCRAPER_DATA_DIR), "html")

        if not os.path.isdir(html_dir):
            self.stderr.write(self.style.ERROR(f"HTML directory not found: {html_dir}"))
            return

        filenames = sorted(f for f in os.listdir(html_dir) if f.endswith(".html"))
        if not filenames:
            self.stdout.write("No HTML files found in data/html/.")
            return

        ids = []
        for fname in filenames:
            stem = fname[:-5]   # strip .html
            if ARXIV_RE.match(stem) or PMC_RE.match(stem):
                ids.append(stem)
            else:
                self.stdout.write(self.style.WARNING(f"  SKIP  {fname}  (unrecognised format)"))

        self.stdout.write(f"Found {len(ids)} paper(s) to process.\n")

        ok = failed = 0
        for paper_id in ids:
            if dry_run:
                self.stdout.write(f"  DRY   {paper_id}")
                continue

            self.stdout.write(f"  →  {paper_id} ... ", ending="")
            try:
                result = resolve_doi_to_paper(paper_id)
                if result.get("status") == "success":
                    title = result.get("paper", {}).get("title", "")
                    self.stdout.write(self.style.SUCCESS(f"OK  {title[:60]}"))
                    ok += 1
                else:
                    msg = result.get("message", "unknown error")
                    self.stdout.write(self.style.WARNING(f"not found  ({msg})"))
                    failed += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"ERROR  {exc}"))
                failed += 1

        if not dry_run:
            self.stdout.write(f"\nDone.  {ok} succeeded, {failed} failed.")
