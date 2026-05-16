
import os
import re
import io
import json
import time
import sys
import gzip
import tarfile
import shutil
import zipfile
import requests
import xml.etree.ElementTree as ET

import concurrent.futures

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from PIL import Image
import matplotlib.pyplot as plt
from tabulate import tabulate

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Import ROB extraction (optional - graceful degradation if not available)
services_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'papers', 'services'))
if os.path.exists(services_path) and services_path not in sys.path:
    sys.path.insert(0, services_path)

try:
    from rob_extraction import extract_rob_artifacts_from_markdown, extract_rob_from_sections_images
    HAS_ROB_MODULE = True
except ImportError:
    HAS_ROB_MODULE = False




# =========================================================
# CONFIG
# =========================================================

BASE_DIR = "paper_pipeline_data"

MD_DIR = os.path.join(BASE_DIR, "md")
PDF_DIR = os.path.join(BASE_DIR, "pdf")
PNG_DIR = os.path.join(BASE_DIR, "png")
HTML_DIR = os.path.join(BASE_DIR, "html")
META_DIR = os.path.join(BASE_DIR, "meta")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
TABLES_DIR = os.path.join(BASE_DIR, "tables")

for d in [MD_DIR, PDF_DIR, PNG_DIR, HTML_DIR, META_DIR, EXPORT_DIR, TABLES_DIR]:
    os.makedirs(d, exist_ok=True)

SESSION = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0"}
MAX_HTTP_RETRIES = 5


# =========================================================
# UTILS
# =========================================================

def normalize(text):
    return re.sub(r"\s+", " ", text or "").strip()


def safe_filename(name):
    return re.sub(r"[^a-zA-Z0-9_\-\.]+", "_", name).strip("_") or "document"


def save_text(data, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path, default=None):
    if not os.path.exists(path):
        return {} if default is None else default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def show_image(path):
    try:
        img = Image.open(path)
        plt.figure()
        plt.imshow(img)
        plt.axis("off")
        plt.show()
    except Exception as e:
        print(f"[IMG ERROR] {e}")


def textify(elem):
    if elem is None:
        return ""

    parts = [elem.text or ""]
    for c in elem:
        parts.append(textify(c))
        if c.tail:
            parts.append(c.tail)

    return normalize("".join(parts))


# =========================================================
# COMMON TABLE PARSING
# =========================================================

def parse_md_table(text):
    lines = [l.strip() for l in text.split("\n") if l.strip().startswith("|")]

    if len(lines) < 2:
        return None

    def split_row(line):
        cells = [x.strip() for x in line.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        return cells

    rows_raw = [split_row(line) for line in lines]

    header = rows_raw[0]
    max_width = len(header)

    data = []
    for r in rows_raw[1:]:
        if all(re.fullmatch(r"-+", cell or "") for cell in r):
            continue

        if len(r) < max_width:
            r += [""] * (max_width - len(r))
        elif len(r) > max_width:
            r = r[:max_width]

        data.append(r)

    return header, data


# =========================================================
# SELENIUM FOR PMC
# =========================================================

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


def fetch_real_html_pmc(pmcid):
    driver = get_driver()
    url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"

    print(f"Opening browser for {pmcid} (Selenium Fallback)...")
    driver.get(url)

    print("Waiting for rendered content / anti-bot redirect...")
    try:
        # Wait up to 15s for the main article wrapper to appear
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//article | //div[contains(@class, 'article')] | //div[@id='mc']"))
        )
        time.sleep(2) # Short buffer for any lazily rendered figure elements
    except Exception as e:
        print(f"[Selenium] Timeout waiting for {pmcid}: {e}")

    html = driver.page_source
    driver.quit()
    return html


# =========================================================
# PMC HELPERS
# =========================================================

def doi_to_pmcid(doi):
    url = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
    params = {"ids": doi, "format": "json"}

    for _ in range(MAX_HTTP_RETRIES):
        try:
            r = SESSION.get(url, params=params, headers=HEADERS, timeout=30)
            data = r.json()
            if data.get("records"):
                return data["records"][0].get("pmcid")
        except Exception:
            pass
        time.sleep(1)

    return None


def fetch_pmc_xml(pmcid):
    pmc_num = pmcid[3:]

    url = "https://pmc.ncbi.nlm.nih.gov/api/oai/v1/mh/"
    params = {
        "verb": "GetRecord",
        "identifier": f"oai:pubmedcentral.nih.gov:{pmc_num}",
        "metadataPrefix": "pmc",
    }

    for _ in range(MAX_HTTP_RETRIES):
        try:
            r = SESSION.get(url, params=params, headers=HEADERS, timeout=60)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        time.sleep(1)

    return None


def extract_pmc_image_urls_from_rendered_html(html):
    """
    Extract figure image URLs from rendered PMC HTML.
    Prefer <figure> / .fig images; fallback to regex.
    """
    soup = BeautifulSoup(html, "html.parser")
    urls = []

    selectors = [
        "figure img",
        ".fig img",
        "div.fig img",
        "img"
    ]

    for selector in selectors:
        for img in soup.select(selector):
            src = img.get("src") or img.get("data-src") or img.get("data-original")
            if not src:
                continue

            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = "https://pmc.ncbi.nlm.nih.gov" + src

            if "cdn.ncbi.nlm.nih.gov/pmc/blobs/" in src and re.search(
                r"\.(jpg|jpeg|png|gif|tif|tiff|webp)(\?|$)", src, re.I
            ):
                urls.append(src)

    if not urls:
        urls = re.findall(
            r'https://cdn\.ncbi\.nlm\.nih\.gov/pmc/blobs/[^"\']+\.(?:jpg|jpeg|png|gif|tif|tiff|webp)(?:\?[^"\']*)?',
            html,
            flags=re.I
        )

    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)

    return out


def download_binary(url, path):
    r = SESSION.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()

    with open(path, "wb") as f:
        f.write(r.content)


def extract_images_from_oa(pmcid):
    """
    Attempts to download and extract images and PDF via the PMC Open Access API tar.gz.
    Returns: (local_image_paths, pdf_path) or (None, None) on failure
    """
    try:
        r = requests.get('https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi', params={"id": pmcid})
        if r.status_code != 200:
            return None, None
            
        root = ET.fromstring(r.text)
        tgz = root.find(".//{*}link[@format='tgz']")
        
        if tgz is None:
            return None, None
            
        href = tgz.attrib.get("href")
        link = f'https{href[3:]}'

        r = requests.get(link, stream=True)

        if r.status_code != 200:
            link = link.replace('https://ftp.ncbi.nlm.nih.gov/pub/pmc/', 'https://ftp.ncbi.nlm.nih.gov/pub/pmc/deprecated/')
            r = requests.get(link, stream=True)

        if r.status_code != 200:
            print(f"[OA API] Failed to download package for {pmcid}: {r.status_code}")
            return None, None
        
        doc_img_dir = os.path.join(PNG_DIR, pmcid)
        os.makedirs(doc_img_dir, exist_ok=True)
        local_paths = []
        pdf_path = None

        # Extract images and PDF from tar.gz
        with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tar:
            for member in tar.getmembers():
                if member.isfile():
                    # Extract images
                    if re.search(r"\.(jpg|jpeg|png|gif|tif|tiff|webp)$", member.name, re.I):
                        f = tar.extractfile(member)
                        if f:
                            filename = os.path.basename(member.name)
                            local_path = os.path.join(doc_img_dir, filename)
                            with open(local_path, "wb") as out_f:
                                out_f.write(f.read())
                            local_paths.append(local_path)
                    # Extract PDF
                    elif re.search(r"\.pdf$", member.name, re.I):
                        f = tar.extractfile(member)
                        if f:
                            pdf_filename = f"{pmcid}.pdf"
                            pdf_path = os.path.join(PDF_DIR, pdf_filename)
                            with open(pdf_path, "wb") as out_f:
                                out_f.write(f.read())
                        
        print(f"[OA API] Successfully extracted {len(local_paths)} images for {pmcid} without Selenium.")
        if pdf_path and os.path.exists(pdf_path):
            print(f"[OA API] Successfully extracted PDF for {pmcid}")
        return sorted(local_paths), pdf_path
    except Exception as e:
        print(f"[OA API] Failed for {pmcid}: {e}")
        return None, None


def download_pmc_images(pmcid):
    """
    Fetch images and PDF via OA API first. Only use Selenium rendered HTML extraction
    as a fallback if the API fails.
    
    Returns: (local_paths, html_path, pdf_path, extraction_method)
      where extraction_method is "oa_api" or "selenium"
      pdf_path is None if extracted via Selenium (fallback)
    """
    # 1. Try fast OA Extraction
    oa_paths, oa_pdf_path = extract_images_from_oa(pmcid)
    
    html_path = os.path.join(HTML_DIR, f"{pmcid}.html")
    if oa_paths is not None:
        save_text("HTML not fetched. OA API was used.", html_path)
        return oa_paths, html_path, oa_pdf_path, "oa_api"

    # 2. Fallback to Selenium
    html = fetch_real_html_pmc(pmcid)

    save_text(html, html_path)

    urls = extract_pmc_image_urls_from_rendered_html(html)
    if not urls:
        return [], html_path, None, "selenium"

    doc_img_dir = os.path.join(PNG_DIR, pmcid)
    os.makedirs(doc_img_dir, exist_ok=True)

    local_paths = []

    for idx, url in enumerate(urls):
        try:
            filename = os.path.basename(urlparse(url).path)
            if not filename or "." not in filename:
                filename = f"pmc_image_{idx}.png"

            local_path = os.path.join(doc_img_dir, filename)

            if not os.path.exists(local_path):
                download_binary(url, local_path)

            local_paths.append(local_path)
            time.sleep(0.3)
        except Exception as e:
            print(f"[PMC IMG FAIL] {url} -> {e}")

    return local_paths, html_path, None, "selenium"


def parse_pmc_table(table):
    if table is None:
        return None

    rows = []

    thead = table.find(".//{*}thead")
    if thead is not None:
        for tr in thead.findall("{*}tr"):
            header_row = [textify(td) for td in tr.findall("{*}th")]
            if header_row:
                rows.append(header_row)

    tbody = table.find(".//{*}tbody")
    if tbody is not None:
        for tr in tbody.findall("{*}tr"):
            body_row = [textify(td) for td in tr.findall("{*}td")]
            if body_row:
                rows.append(body_row)

    if not rows:
        # fallback: try plain tr
        for tr in table.findall(".//{*}tr"):
            cells = [textify(td) for td in tr.findall("{*}th")] + [textify(td) for td in tr.findall("{*}td")]
            if cells:
                rows.append(cells)

    if not rows:
        return None

    header = rows[0]

    md = []
    md.append("| " + " | ".join(header) + " |")
    md.append("| " + " | ".join("---" for _ in header) + " |")

    for r in rows[1:]:
        if len(r) < len(header):
            r += [""] * (len(header) - len(r))
        elif len(r) > len(header):
            r = r[:len(header)]
        md.append("| " + " | ".join(r) + " |")

    return "\n".join(md)


def parse_pmc_article_to_markdown(xml):
    """
    Build markdown from PMC XML.
    Figures are inserted as placeholders:
    ![caption](PMC_FIG_0), ![caption](PMC_FIG_1), ...
    Later interactive_view maps them to downloaded local files.
    """
    root = ET.fromstring(xml)
    article = root.find(".//{*}article")

    if article is None:
        return None

    out = []

    title = article.find(".//{*}article-title")
    if title is not None:
        out.append(f"# {textify(title)}\n")

    body = article.find("{*}body")
    if body is None:
        return "\n".join(out)

    fig_counter = 0

    for sec in body.findall(".//{*}sec"):
        sec_title = sec.find("{*}title")
        if sec_title is not None:
            out.append(f"\n## {textify(sec_title)}\n")

        # paragraph text directly under this section
        for p in sec.findall("{*}p"):
            txt = textify(p)
            if txt:
                out.append(txt + "\n")

        # figures under this section
        for fig in sec.findall(".//{*}fig"):
            label = textify(fig.find("{*}label"))
            caption = textify(fig.find(".//{*}caption"))
            alt = normalize(f"{label} {caption}")

            out.append(f"\n![{alt}](PMC_FIG_{fig_counter})\n")
            fig_counter += 1

        # tables under this section
        for tbl_wrap in sec.findall(".//{*}table-wrap"):
            label = tbl_wrap.find("{*}label")
            caption = tbl_wrap.find(".//{*}caption")
            table = tbl_wrap.find("{*}table")

            if label is not None:
                out.append(f"\n**{textify(label)}**\n")

            if caption is not None:
                out.append(f"*{textify(caption)}*\n")

            md_table = parse_pmc_table(table)
            if md_table:
                out.append(md_table + "\n")

    return "\n".join(out)


def clean_markdown(md_text):
    lines = md_text.split("\n")

    cleaned = []
    current_section = None
    current_content = []
    seen_sections = set()

    def flush():
        nonlocal current_section, current_content

        if current_section:
            content = "\n".join(current_content).strip()
            if content:
                key = normalize(current_section.lower() + content[:200])
                if key not in seen_sections:
                    seen_sections.add(key)
                    cleaned.append(current_section)
                    cleaned.append(content)
                    cleaned.append("")

        current_section = None
        current_content = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("## "):
            flush()
            current_section = stripped
        else:
            if current_section:
                current_content.append(line)
            else:
                cleaned.append(line)

    flush()
    return "\n".join(cleaned)


def extract_pmc_authors_emails(xml):
    root = ET.fromstring(xml)

    authors = []
    emails = []

    for c in root.findall(".//{*}contrib[@contrib-type='author']"):
        g = c.find(".//{*}given-names")
        s = c.find(".//{*}surname")

        if g is not None and s is not None:
            authors.append(normalize(f"{g.text} {s.text}"))

        e = c.find(".//{*}email")
        if e is not None and e.text:
            emails.append(normalize(e.text))

    authors = list(dict.fromkeys([a for a in authors if a]))
    emails = list(dict.fromkeys([e for e in emails if e]))

    return authors, emails


# =========================================================
# ARXIV HELPERS
# =========================================================

def is_arxiv_identifier(text):
    low = text.lower()
    return "arxiv" in low or re.search(r"\b\d{4}\.\d{4,5}(v\d+)?\b", low) is not None


def doi_to_arxiv_id(doi):
    # Handles e.g. arXiv:2501.12345, arxiv.org/abs/2501.12345, doi-like strings containing arxiv
    m = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", doi, flags=re.I)
    if m:
        return m.group(1)
    return None


def fetch_ar5iv_html(arxiv_id):
    url = f"https://ar5iv.org/html/{arxiv_id}"

    for _ in range(MAX_HTTP_RETRIES):
        try:
            r = SESSION.get(url, headers=HEADERS, timeout=60)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        time.sleep(1)

    return None


def download_arxiv_source(arxiv_id):
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    r = SESSION.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.content


def unpack_archive(content):
    files = {}

    try:
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:*") as tar:
            for member in tar.getmembers():
                if member.isfile() and member.name.lower().endswith(".tex"):
                    extracted = tar.extractfile(member)
                    if extracted is None:
                        continue
                    files[member.name] = extracted.read().decode("utf-8", errors="ignore")
        if files:
            return files
    except tarfile.ReadError:
        pass

    try:
        text = gzip.decompress(content).decode("utf-8", errors="ignore")
        return {"main.tex": text}
    except Exception:
        return {}


def download_single_image(url, doc_id, idx):
    if url.startswith("/"):
        url = "https://ar5iv.org" + url

    img_dir = os.path.join(PNG_DIR, doc_id)
    os.makedirs(img_dir, exist_ok=True)

    try:
        filename = os.path.basename(urlparse(url).path)
        if not filename or "." not in filename:
            filename = f"image_{idx}.png"

        path = os.path.join(img_dir, filename)

        if not os.path.exists(path):
            r = SESSION.get(url, headers=HEADERS, timeout=30)
            if r.status_code != 200:
                return None
            with open(path, "wb") as f:
                f.write(r.content)

        return path
    except Exception:
        return None


# =========================================================
# ARXIV HTML -> MD
# =========================================================

def parse_html_table(table):
    rows = []

    for tr in table.find_all("tr"):
        cols = tr.find_all(["td", "th"])
        row = [normalize(c.get_text(" ", strip=True)) for c in cols]
        if row:
            rows.append(row)

    if not rows:
        return ""

    md = []
    md.append("| " + " | ".join(rows[0]) + " |")
    md.append("| " + " | ".join("---" for _ in rows[0]) + " |")

    for r in rows[1:]:
        if len(r) < len(rows[0]):
            r += [""] * (len(rows[0]) - len(r))
        elif len(r) > len(rows[0]):
            r = r[:len(rows[0])]
        md.append("| " + " | ".join(r) + " |")

    return "\n".join(md)


def parse_html_figure(fig):
    img = fig.find("img")
    caption = fig.find("figcaption")

    src = ""
    if img and img.has_attr("src"):
        src = img["src"]
        if src.startswith("/"):
            src = "https://ar5iv.org" + src

    cap = caption.get_text(" ", strip=True) if caption else ""
    return f"\n![{cap}]({src})\n"


def html_to_markdown_arxiv(html):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article")

    if not article:
        return None

    md = []

    for tag in article.find_all([
        "h1", "h2", "h3",
        "p", "li", "pre",
        "figure", "table"
    ]):
        text = normalize(tag.get_text(" ", strip=True))

        if tag.name == "h1":
            md.append(f"# {text}")
        elif tag.name == "h2":
            md.append(f"\n## {text}")
        elif tag.name == "h3":
            md.append(f"\n### {text}")
        elif tag.name == "p":
            if text:
                md.append(text)
        elif tag.name == "li":
            md.append(f"- {text}")
        elif tag.name == "pre":
            md.append(f"\n```\n{text}\n```")
        elif tag.name == "figure":
            md.append(parse_html_figure(tag))
        elif tag.name == "table":
            table_md = parse_html_table(tag)
            if table_md:
                md.append("\n" + table_md + "\n")

    return "\n\n".join(md)


# =========================================================
# ARXIV AUTHORS / EMAILS FROM TEX
# =========================================================

def extract_balanced_blocks(text, command):
    results = []
    pattern = re.compile(rf"\\{re.escape(command)}\s*\{{")

    for match in pattern.finditer(text):
        brace_start = match.end() - 1
        depth = 0
        end = None

        for i in range(brace_start, len(text)):
            char = text[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break

        if end is not None:
            results.append(text[brace_start + 1:end])

    return results


def find_author_files(files):
    author_files = {}

    for filename, tex in files.items():
        blocks = extract_balanced_blocks(tex, "author")
        if blocks:
            author_files[filename] = blocks

    return author_files


def normalize_author_name(name):
    name = name.strip()
    name = re.sub(r"^(?:AND|And|and)\s+", "", name)
    name = re.sub(r"(?<=[A-Za-z])\s*\d{4}-\d{4}-\d{4}-\d{3,4}[0-9X]\b", "", name)
    name = re.sub(r"\b\d{4}-\d{4}-\d{4}-\d{3,4}[0-9X]\b", "", name)
    name = re.sub(r"\s*\.\s*mm\s*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+mm\s*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"[^A-Za-z.\-'\s]", " ", name)
    name = re.sub(r"(?:\s*-\s*){2,}X?\s*$", "", name)
    name = re.sub(r"-{2,}X?\s*$", "", name)
    name = re.sub(r"(?:\s*-\s*)+X\s*$", "", name)
    name = re.sub(r"\s*-\s*$", "", name)
    name = re.sub(r"[-–—\s]+$", "", name)
    name = re.sub(r"\s+", " ", name).strip(" ,;")
    return name


def looks_like_person_name(line):
    line = line.strip(" ,;")
    if not line or "@" in line:
        return False

    low = line.lower()

    bad_keywords = [
        "university", "department", "institute", "school", "centre", "center",
        "lab", "labs", "laboratory", "faculty", "college",
        "research", "brain", "google", "openai", "meta", "microsoft",
        "amazon", "deepmind", "anthropic", "nvidia",
        "economics", "business", "law",
        "corresponding author", "email", "orcid", "https", "http"
    ]
    if any(k in low for k in bad_keywords):
        return False

    words = line.split()
    if len(words) < 2 or len(words) > 6:
        return False

    valid_words = 0
    for word in words:
        cleaned = re.sub(r"[^A-Za-z.\-']", "", word)
        if not cleaned:
            continue
        if cleaned[0].isupper():
            valid_words += 1

    if valid_words < 2:
        return False

    if len(line) > 60:
        return False

    return True


def clean_single_author_block(block):
    text = block.replace("\r", "\n")

    text = text.replace("\\\\", "\n")
    text = re.sub(r"\\and\b|\\And\b|\\AND\b", "\n", text)
    text = re.sub(r"\\quad\b|\\qquad\b", "\n", text)
    text = re.sub(r"\s+\band\b\s+", "\n", text, flags=re.IGNORECASE)

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\\thanks\s*\{([^{}]|\{[^{}]*\})*\}", "", text)

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\\footnote\s*\{([^{}]|\{[^{}]*\})*\}", "", text)

    text = re.sub(r"\$\^\{[^$]*\}\$", "", text)
    text = re.sub(r"\$[^$]*\$", "", text)

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\\[A-Za-z*]+\s*\{([^{}]*)\}", r"\1", text)

    text = re.sub(r"\\[A-Za-z*]+", " ", text)
    text = text.replace("{", "").replace("}", "")

    raw_lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip(" ,;")
        if line:
            raw_lines.append(line)

    candidates = []

    for line in raw_lines:
        comma_parts = [p.strip() for p in re.split(r"\s*,\s*", line) if p.strip()]
        normalized_parts = [normalize_author_name(p) for p in comma_parts]

        if len(comma_parts) > 1 and all(looks_like_person_name(p) for p in normalized_parts):
            candidates.extend(normalized_parts)
        else:
            candidates.append(normalize_author_name(line))

    authors = []
    seen = set()

    for cand in candidates:
        cand = normalize_author_name(cand)
        if looks_like_person_name(cand):
            key = cand.lower()
            if key not in seen:
                seen.add(key)
                authors.append(cand)

    return authors


def extract_emails_from_text(tex):
    emails = []

    grouped = re.findall(r"\{([^{}]+)\}\\?@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})", tex)
    for users, domain in grouped:
        for user in users.split(","):
            user = user.strip().strip("\\")
            if user:
                emails.append(f"{user}@{domain}")

    normal = re.findall(
        r"[A-Za-z0-9._%+\-]+\\?@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
        tex,
    )
    emails.extend(normal)

    cleaned = []
    seen = set()
    for email in emails:
        email = email.replace("\\@", "@").strip(".,;:()[]{}<> ")
        key = email.lower()
        if key and key not in seen:
            seen.add(key)
            cleaned.append(email)

    return cleaned


def collect_authors_and_emails(files):
    author_files = find_author_files(files)
    if not author_files:
        return [], []

    all_authors = []
    all_emails = []

    for filename, author_blocks in author_files.items():
        for block in author_blocks:
            authors = clean_single_author_block(block)
            all_authors.extend(authors)

        all_emails.extend(extract_emails_from_text(files[filename]))

    dedup_authors = []
    seen_authors = set()
    for author in all_authors:
        key = re.sub(r"\s+", " ", author.strip().lower())
        if key and key not in seen_authors:
            seen_authors.add(key)
            dedup_authors.append(author.strip())

    dedup_emails = []
    seen_emails = set()
    for email in all_emails:
        key = email.lower().strip()
        if key and key not in seen_emails:
            seen_emails.add(key)
            dedup_emails.append(email.strip())

    return dedup_authors, dedup_emails


# =========================================================
# COMMON MARKDOWN PARSER FOR INTERACTIVE VIEW
# =========================================================

def parse_markdown(md_text):
    title = ""
    sections = []
    current = None
    current_table = []
    recent_lines = []

    def flush_table():
        nonlocal current_table, current

        if current and current_table:
            idx = len(current["tables"])
            current["tables"].append("\n".join(current_table))
            current["text"] += f" [[TABLE_{idx}]] "
            current_table.clear()

    for line in md_text.split("\n"):
        stripped = line.strip()

        if not stripped:
            flush_table()
            continue

        if stripped.startswith("# ") and not title:
            title = normalize(stripped[2:])
            recent_lines.append(line)
            continue

        if re.match(r"^##+\s+", stripped):
            flush_table()
            if current:
                sections.append(current)

            heading = re.sub(r"^##+\s*", "", stripped)

            if heading.lower() in ["authors", "emails"]:
                current = None
                continue

            current = {"heading": heading, "text": "", "tables": []}
            recent_lines.append(line)
            continue

        if stripped.startswith("|"):
            current_table.append(stripped)
            continue

        flush_table()

        if current:
            current["text"] += " " + line

        recent_lines.append(line)
        if len(recent_lines) > 10:
            recent_lines.pop(0)

    flush_table()

    if current:
        sections.append(current)

    return title, sections


def clean_sections(sections):
    return [s for s in sections if len(normalize(s["text"])) > 5 or s["tables"]]


# =========================================================
# IMAGE RESOLUTION IN VIEWER
# =========================================================

def resolve_section_images(section_text, doc):
    """
    Returns list of image entries:
    [
        {"placeholder": "PMC_FIG_0", "path": "...", "caption": "..."},
        {"placeholder": "https://...", "path": "...", "caption": "..."},
        ...
    ]
    """
    img_entries = []
    matches = re.findall(r'!\[(.*?)\]\((.*?)\)', section_text)

    if not matches:
        return img_entries

    source = doc.get("source")
    paper_id = doc.get("paper_id", "doc")

    if source == "pmc":
        local_images = doc.get("local_images", [])

        for alt, ref in matches:
            if ref.startswith("PMC_FIG_"):
                m = re.search(r"PMC_FIG_(\d+)", ref)
                if m:
                    idx = int(m.group(1))
                    path = local_images[idx] if idx < len(local_images) else None
                    img_entries.append({
                        "placeholder": ref,
                        "path": path,
                        "caption": alt
                    })

    elif source == "arxiv":
        for i, (alt, ref) in enumerate(matches):
            path = download_single_image(ref, paper_id, i)
            img_entries.append({
                "placeholder": ref,
                "path": path,
                "caption": alt
            })

    return img_entries


# =========================================================
# EXPORT SELECTED CONTENT
# =========================================================

def init_export(doc):
    paper_id = safe_filename(doc.get("paper_id", "document"))
    out_dir = os.path.join(EXPORT_DIR, paper_id)
    img_dir = os.path.join(out_dir, "images")
    json_path = os.path.join(out_dir, "content.json")

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)

    data = load_json(json_path, default={
        "title": "",
        "authors": [],
        "emails": [],
        "sections": {}
    })

    if "title" not in data:
        data["title"] = ""
    if "authors" not in data:
        data["authors"] = []
    if "emails" not in data:
        data["emails"] = []
    if "sections" not in data or not isinstance(data["sections"], dict):
        data["sections"] = {}

    return out_dir, img_dir, json_path, data


def extract_clean_section_text(section_text):
    text_only = re.sub(r'\[\[TABLE_\d+\]\]', '', section_text)
    text_only = re.sub(r'!\[.*?\]\(.*?\)', '', text_only)
    return normalize(text_only)


def copy_section_images(image_entries, img_dir):
    saved_images = []
    seen = set()

    for img in image_entries:
        src = img.get("path")
        if not src or not os.path.exists(src):
            continue

        fname = os.path.basename(src)
        base, ext = os.path.splitext(fname)
        dst = os.path.join(img_dir, fname)

        counter = 1
        while os.path.exists(dst) and os.path.abspath(src) != os.path.abspath(dst):
            fname = f"{base}_{counter}{ext}"
            dst = os.path.join(img_dir, fname)
            counter += 1

        if not os.path.exists(dst):
            shutil.copy2(src, dst)

        rel_path = os.path.join("images", os.path.basename(dst)).replace("\\", "/")
        if rel_path not in seen:
            seen.add(rel_path)
            saved_images.append(rel_path)

    return saved_images


def save_selected_section(doc, article_title, sec, image_entries):
    out_dir, img_dir, json_path, data = init_export(doc)

    if not data["title"]:
        data["title"] = article_title

    if not data["authors"]:
        data["authors"] = doc.get("authors", [])

    if not data["emails"]:
        data["emails"] = doc.get("emails", [])

    section_name = sec["heading"]

    if section_name in data["sections"]:
        print(f"[SKIP] Section already saved: {section_name}")
        return False, json_path

    text_only = extract_clean_section_text(sec["text"])
    tables = list(sec.get("tables", []))
    saved_images = copy_section_images(image_entries, img_dir)

    data["sections"][section_name] = {
        "text": text_only,
        "tables": tables,
        "images": saved_images
    }

    save_json(data, json_path)
    print(f"[SAVED] Section exported: {section_name}")
    return True, json_path


def zip_export(doc):
    paper_id = safe_filename(doc.get("paper_id", "document"))
    out_dir = os.path.join(EXPORT_DIR, paper_id)

    if not os.path.exists(out_dir):
        print("[ZIP] Nothing to zip.")
        return None

    zip_path = os.path.join(EXPORT_DIR, f"{paper_id}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(out_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, out_dir)
                zipf.write(full_path, rel_path)

    print(f"[ZIP CREATED] {zip_path}")
    return zip_path


def extract_and_save_tables(doc):
    """
    Extract all tables from a document's markdown and save them to TABLES_DIR as CSV.
    Folder structure matches other directories (png, md): tables/{pmcid or arxiv_id}/
    Returns list of table info dicts with path, section, and index.
    """
    md_path = doc.get("md")
    if not md_path or not os.path.exists(md_path):
        return []
    
    # Use pmcid or arxiv_id for consistent folder naming (like PNG_DIR does)
    doc_id = doc.get("pmcid") or doc.get("arxiv_id")
    if not doc_id:
        return []
    
    doc_dir = os.path.join(TABLES_DIR, doc_id)
    os.makedirs(doc_dir, exist_ok=True)
    
    saved_tables = []
    
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        
        _, sections = parse_markdown(md_text)
        
        table_counter = 0
        for section in sections:
            for table_idx, table_md in enumerate(section.get("tables", [])):
                parsed = parse_md_table(table_md)
                if parsed:
                    header, rows = parsed
                    
                    table_filename = f"table_{table_counter}.csv"
                    table_path = os.path.join(doc_dir, table_filename)
                    
                    # Save as CSV
                    with open(table_path, "w", encoding="utf-8", newline="") as f:
                        writer = __import__("csv").writer(f)
                        writer.writerow(header)
                        writer.writerows(rows)
                    
                    saved_tables.append({
                        "path": table_path,
                        "section": section.get("heading"),
                        "table_index": table_idx,
                        "global_index": table_counter
                    })
                    table_counter += 1
    except Exception as e:
        print(f"[TABLES] Error extracting tables from {doc.get('paper_id')}: {e}")
    
    return saved_tables


def export_all_processed_json(processed, out_dir=EXPORT_DIR, filename=None):
    """Save a single JSON file containing all processed documents,
    storing only paths to markdown/html files (no inline content).
    Also extracts and saves all tables to TABLES_DIR.
    """
    if not filename:
        filename = f"processed_export_{int(time.time())}.json"

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    
    # Extract and save tables for all documents
    total_tables = 0
    for doc in processed:
        saved_tables = extract_and_save_tables(doc)
        total_tables += len(saved_tables)

    out = []
    for doc in processed:
        entry = dict(doc)

        # Keep only references to the md/html file paths instead of embedding contents
        md_path = doc.get("md")
        entry["md_path"] = md_path if md_path else None

        html_path = doc.get("html")
        entry["html_path"] = html_path if html_path else None

        # Add table CSV paths
        saved_tables = extract_and_save_tables(doc)
        entry["table_csv_paths"] = saved_tables
        total_tables = sum(len(extract_and_save_tables(d)) for d in processed)
        # Extract tables from markdown sections (so tables are present similar to images)
        
        # Add table CSV paths
        saved_tables = extract_and_save_tables(doc)
        entry["table_csv_paths"] = saved_tables

        # Extract tables from markdown sections (so tables are present similar to images)
        entry_sections = []
        if md_path and os.path.exists(md_path):
            # Add table CSV paths
            saved_tables = extract_and_save_tables(doc)
            entry["table_csv_paths"] = saved_tables

        # Extract tables from markdown sections (so tables are present similar to images)
        entry_sections = []
        if md_path and os.path.exists(md_path):
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    md_text = f.read()
                _, sections = parse_markdown(md_text)
                local_images = doc.get("local_images", [])
                for s in sections:
                    # Tables: parse markdown tables into structured header/rows for easy re-import
                    tables_struct = []
                    for tbl_md in s.get("tables", []):
                        parsed = parse_md_table(tbl_md)
                        if parsed:
                            header, rows = parsed
                            tables_struct.append({
                                "header": header,
                                "rows": rows,
                                "markdown": tbl_md
                            })
                        else:
                            tables_struct.append({
                                "header": None,
                                "rows": None,
                                "markdown": tbl_md
                            })

                    # Images: map markdown image placeholders/refs to local paths when possible
                    images = []
                    try:
                        matches = re.findall(r'!\[(.*?)\]\((.*?)\)', s.get("text", ""))
                        for alt, ref in matches:
                            img_entry = {"placeholder": ref, "caption": alt, "path": None}
                            if ref.startswith("PMC_FIG_"):
                                m = re.search(r"PMC_FIG_(\d+)", ref)
                                if m:
                                    idx = int(m.group(1))
                                    if idx < len(local_images):
                                        img_entry["path"] = local_images[idx]
                            else:
                                # For direct URLs or other refs, leave placeholder and path empty
                                img_entry["path"] = None
                            images.append(img_entry)
                    except Exception:
                        images = []

                    entry_sections.append({
                        "heading": s.get("heading"),
                        "tables": tables_struct,
                        "images": images
                    })
            except Exception:
                entry_sections = []

        entry["sections"] = entry_sections
        
        # Extract ROB artifacts from markdown and images
        if HAS_ROB_MODULE and md_path and os.path.exists(md_path):
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    md_text = f.read()
                entry["rob_artifacts"] = extract_rob_artifacts_from_markdown(
                    md_text,
                    paper_id=doc.get("paper_id"),
                )
            except Exception:
                pass

        if HAS_ROB_MODULE and entry_sections:
            try:
                ocr_artifacts = extract_rob_from_sections_images(entry_sections, paper_id=doc.get("paper_id"))
                if ocr_artifacts:
                    # Merge OCR artifacts with existing ROB artifacts
                    existing_artifacts = entry.get("rob_artifacts", [])
                    entry["rob_artifacts"] = existing_artifacts + ocr_artifacts
            except Exception:
                pass

        out.append(entry)

    save_json(out, path)
    print(f"[EXPORT ALL] Saved {len(out)} entries to {path}")
    print(f"[EXPORT ALL] Saved {total_tables} tables to {TABLES_DIR}")
    
    # Create list of papers with ROB artifacts (DOIs only, one per line)
    rob_papers = []
    oa_only_rob_papers = []  # Papers extracted via OA API (no Selenium) with ROB
    
    for doc in out:
        if doc.get("rob_artifacts"):
            paper_id = doc.get("paper_id")
            rob_papers.append(paper_id)
            
            # Check if paper was extracted via OA API (not Selenium)
            extraction_method = doc.get("extraction_method", "")
            if extraction_method == "oa_api":
                oa_only_rob_papers.append(paper_id)
    
    # Save simple ROB papers list (DOIs only, one per line)
    if rob_papers:
        rob_list_filename = filename.replace(".json", "_rob_dois.txt")
        rob_list_path = os.path.join(out_dir, rob_list_filename)
        
        with open(rob_list_path, "w", encoding="utf-8") as f:
            for paper_id in rob_papers:
                f.write(f"{paper_id}\n")
        
        print(f"[EXPORT ALL] Saved {len(rob_papers)} ROB paper DOIs to {rob_list_path}")
    
    # Save OA-only ROB papers list (DOIs only, no Selenium needed)
    if oa_only_rob_papers:
        oa_rob_list_filename = filename.replace(".json", "_rob_oa_only_dois.txt")
        oa_rob_list_path = os.path.join(out_dir, oa_rob_list_filename)
        
        with open(oa_rob_list_path, "w", encoding="utf-8") as f:
            for paper_id in oa_only_rob_papers:
                f.write(f"{paper_id}\n")
        
        print(f"[EXPORT ALL] Saved {len(oa_only_rob_papers)} OA-only ROB paper DOIs to {oa_rob_list_path}")
    
    return path


def export_rob_tables_for_inspection(processed, out_dir=EXPORT_DIR, filename=None):
    """
    Export ROB tables from papers in a format suitable for easy inspection and comparison.
    Each entry contains:
    - DOI, md_path, pdf_path, extraction_method
    - ROB tables with headers and rows for side-by-side comparison
    
    Output: JSON with structure:
    [
      {
        "doi": "10.1234/...",
        "md_path": "path/to/md",
        "pdf_path": "path/to/pdf",
        "extraction_method": "oa_api" or "selenium",
        "rob_tables": [
          {
            "section": "Risk of Bias Assessment",
            "table_index": 0,
            "headers": ["Study", "Selection", "Performance", ...],
            "rows": [
              ["Study Name", "high", "low", ...],
              ...
            ],
            "markdown": "| Study | ... |"
          }
        ]
      }
    ]
    """
    if not filename:
        filename = f"rob_tables_inspection_{int(time.time())}.json"
    
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    
    out = []
    papers_with_tables = 0
    
    for doc in processed:
        # Skip if no ROB artifacts
        if not doc.get("rob_artifacts"):
            continue
        
        entry = {
            "doi": doc.get("paper_id"),
            "md_path": doc.get("md"),
            "pdf_path": doc.get("pdf_path"),
            "extraction_method": doc.get("extraction_method"),
            "rob_tables": []
        }
        
        # Extract table artifacts with actual table data
        md_path = doc.get("md")
        if md_path and os.path.exists(md_path):
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    md_text = f.read()
                
                # Find all markdown tables in the ROB artifacts sections
                for artifact in doc.get("rob_artifacts", []):
                    if artifact.get("artifact_type") == "table":
                        md_table = artifact.get("markdown", "")
                        if md_table:
                            parsed = parse_md_table(md_table)
                            if parsed:
                                header, rows = parsed
                                entry["rob_tables"].append({
                                    "section": artifact.get("section", "Unknown"),
                                    "table_index": len(entry["rob_tables"]),
                                    "headers": header,
                                    "rows": rows,
                                    "markdown": md_table,
                                    "normalized_records": artifact.get("normalized_records", [])
                                })
            except Exception as e:
                print(f"[ROB TABLES] Error extracting tables from {doc.get('paper_id')}: {e}")
        
        # Only include papers that have extracted ROB tables
        if entry["rob_tables"]:
            out.append(entry)
            papers_with_tables += 1
    
    save_json(out, path)
    print(f"[ROB TABLES EXPORT] Saved {papers_with_tables} papers with {sum(len(p.get('rob_tables', [])) for p in out)} ROB tables to {path}")
    return path


# =========================================================
# VIEW
# =========================================================

def interactive_view(doc):
    md_path = doc["md"]

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    title, sections = parse_markdown(md_text)
    sections = clean_sections(sections)

    print(f"\nDocument: {title}\n")

    print("Source:")
    print(f"- {doc.get('source', 'unknown')}")

    print("\nAuthors:")
    if doc.get("authors"):
        for a in doc["authors"]:
            print(f"- {a}")
    else:
        print("- Not found")

    print("\nEmails:")
    if doc.get("emails"):
        for i, e in enumerate(doc["emails"]):
            print(f"- {e}" + (" (corresponding)" if i == 0 else ""))
    else:
        print("- Not found")

    while True:
        print("\nAvailable sections:\n")
        for i, sec in enumerate(sections):
            print(f"{i+1}. {sec['heading']}")

        choice = input("\nSelect section (or 'n'): ").lower().strip()

        if choice in ["n", "q", "quit", "exit"]:
            create_zip = input("Create ZIP from already exported content? (y/n): ").lower().strip()
            if create_zip == "y":
                zip_export(doc)
            break

        if not choice.isdigit():
            continue

        idx = int(choice) - 1
        if idx < 0 or idx >= len(sections):
            continue

        sec = sections[idx]
        content = sec["text"]

        print(f"\n--- {sec['heading']} ---\n")

        text_only = re.sub(r'\[\[TABLE_\d+\]\]', '', content)
        text_only = re.sub(r'!\[.*?\]\(.*?\)', '', text_only)
        print(normalize(text_only).strip())

        # IMAGES
        image_entries = resolve_section_images(content, doc)
        for i, img in enumerate(image_entries):
            if img["path"] and os.path.exists(img["path"]):
                print(f"\n[Image {i+1}] {img['caption']}")
                print(f"Path: {img['path']}\n")
                show_image(img["path"])
            else:
                print(f"\n[Image {i+1}] Not available: {img['caption']}")

        # TABLES
        for table_text in sec["tables"]:
            parsed = parse_md_table(table_text)
            if parsed:
                header, rows = parsed

                def clean_cell(x):
                    if not x:
                        return ""
                    x = x.replace("\\%", "%")
                    x = x.replace("\\pm", "±")
                    x = re.sub(r"\s+", " ", x).strip()

                    dup_match = re.match(r"^(.*?)\s+\1$", x)
                    if dup_match:
                        x = dup_match.group(1)

                    return x

                header = [clean_cell(h) for h in header]
                rows = [[clean_cell(c) for c in r] for r in rows]

                print("\n[Table]\n")
                print(tabulate(rows, headers=header, tablefmt="fancy_grid"))

        save_choice = input("\nSave this section to JSON export? (y/n): ").lower().strip()
        if save_choice == "y":
            save_selected_section(doc, title, sec, image_entries)

        again = input("\nAnything else? (y/n): ").lower().strip()
        if again != "y":
            make_zip = input("Create ZIP now? (y/n): ").lower().strip()
            if make_zip == "y":
                zip_export(doc)
            break


# =========================================================
# PROCESS PMC
# =========================================================

def process_pmc(doi):
    pmcid = doi_to_pmcid(doi)
    if not pmcid:
        return None

    print(f"[PMC] PMCID found: {pmcid}")

    xml = fetch_pmc_xml(pmcid)
    if not xml:
        return None

    authors, emails = extract_pmc_authors_emails(xml)

    md = parse_pmc_article_to_markdown(xml)
    if not md:
        return None

    md = clean_markdown(md)

    local_images, html_path, pdf_path, extraction_method = download_pmc_images(pmcid)

    md_path = os.path.join(MD_DIR, f"{pmcid}.md")
    meta_path = os.path.join(META_DIR, f"{pmcid}.json")

    save_text(md, md_path)

    meta = {
        "paper_id": doi,
        "source": "pubmed",
        "pmcid": pmcid,
        "md": md_path,
        "html": html_path,
        "pdf_path": pdf_path,
        "authors": authors,
        "emails": emails,
        "local_images": local_images,
        "extraction_method": extraction_method
    }
    save_json(meta, meta_path)

    return meta


# =========================================================
# PROCESS ARXIV
# =========================================================

def process_arxiv(doi):
    arxiv_id = doi_to_arxiv_id(doi)
    if not arxiv_id:
        return None

    print(f"[arXiv] ID found: {arxiv_id}")

    html = fetch_ar5iv_html(arxiv_id)
    if not html:
        return None

    md = html_to_markdown_arxiv(html)
    if not md:
        return None

    try:
        source = download_arxiv_source(arxiv_id)
        files = unpack_archive(source)
        authors, emails = collect_authors_and_emails(files)
    except Exception:
        authors, emails = [], []

    md_path = os.path.join(MD_DIR, f"{arxiv_id}.md")
    meta_path = os.path.join(META_DIR, f"{arxiv_id}.json")

    save_text(md, md_path)

    meta = {
        "paper_id": doi,
        "source": "arxiv",
        "arxiv_id": arxiv_id,
        "md": md_path,
        "authors": authors,
        "emails": emails,
        "local_images": []
    }
    save_json(meta, meta_path)

    return meta


# =========================================================
# ROUTER
# =========================================================

def process_document(doi):
    doi = doi.strip()

    if not doi:
        return None

    if is_arxiv_identifier(doi):
        return process_arxiv(doi)

    pmc_result = process_pmc(doi)
    if pmc_result:
        return pmc_result

    return None


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    doi_input = input("DOIs / arXiv IDs: ").strip()
    inputs = [d.strip() for d in doi_input.split(",") if d.strip()]

    processed = []
    success = 0
    failed = 0

    print(f"\nProcessing {len(inputs)} document(s) concurrently...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_item = {executor.submit(process_document, item): item for item in inputs}
        
        for future in concurrent.futures.as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                if result:
                    processed.append(result)
                    success += 1
                else:
                    failed += 1
                    print(f"[FAIL] {item}")
            except Exception as e:
                failed += 1
                print(f"[ERROR] {item}: {e}")

    print("\n==== SUMMARY ====")
    print(f"Processed successfully: {success}")
    print(f"Failed: {failed}")
    print(f"Total: {len(inputs)}")

    if not processed:
        raise SystemExit

    # Offer to export all processed documents into a single JSON file
    try:
        export_choice = input("Export all processed documents to a single JSON file? (y/n): ").lower().strip()
        if export_choice == "y":
            export_all_processed_json(processed)
    except Exception:
        pass

    while True:
        print("\nProcessed documents:\n")
        for i, doc in enumerate(processed):
            print(f"{i+1}. {doc['paper_id']} [{doc['source']}]")

        c = input("\nSelect doc (or 'n'): ").lower().strip()
        if c in ["n", "q", "quit", "exit"]:
            break

        if not c.isdigit():
            continue

        idx = int(c) - 1
        if idx < 0 or idx >= len(processed):
            continue

        interactive_view(processed[idx])
