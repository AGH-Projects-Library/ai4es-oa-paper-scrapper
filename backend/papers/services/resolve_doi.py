import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from bs4 import BeautifulSoup


# CONFIG

BASE = "data"

PDF_DIR = os.path.join(BASE, "pdf")
XML_DIR = os.path.join(BASE, "xml")
MD_DIR = os.path.join(BASE, "md")
TMP_DIR = os.path.join(BASE, "tmp")

for d in [PDF_DIR, XML_DIR, MD_DIR, TMP_DIR]:
    os.makedirs(d, exist_ok=True)

SESSION = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0"}

MAX_HTTP_RETRIES = 5


# GENERAL HELPERS

def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def save_text(data, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)


# ARXIV

def is_arxiv_doi(doi: str):
    return "arxiv" in doi.lower()


def doi_to_arxiv_id(doi):
    m = re.search(r"arxiv[:./]?(\d+\.\d+)", doi.lower())
    return m.group(1) if m else None


def download_arxiv_pdf(arxiv_id):
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    for _ in range(MAX_HTTP_RETRIES):
        try:
            r = SESSION.get(url, headers=HEADERS, timeout=60)
            if r.status_code == 200 and r.content:
                return r.content
        except:
            pass
        time.sleep(1)

    return None


def fetch_ar5iv_html(arxiv_id):
    url = f"https://ar5iv.org/html/{arxiv_id}"

    for _ in range(MAX_HTTP_RETRIES):
        try:
            r = SESSION.get(url, headers=HEADERS, timeout=60)
            if r.status_code == 200 and r.text:
                return r.text
        except:
            pass
        time.sleep(1)

    return None


def parse_table(table):
    rows = []
    for tr in table.find_all("tr"):
        cols = tr.find_all(["td", "th"])
        row = [normalize(c.get_text(" ", strip=True)) for c in cols]
        if row:
            rows.append(row)

    if not rows:
        return ""

    header = rows[0]
    md = []
    md.append("| " + " | ".join(header) + " |")
    md.append("| " + " | ".join("---" for _ in header) + " |")

    for r in rows[1:]:
        if len(r) < len(header):
            r += [""] * (len(header) - len(r))
        md.append("| " + " | ".join(r) + " |")

    return "\n".join(md)


def parse_figure(fig):
    img = fig.find("img")
    caption = fig.find("figcaption")

    src = ""
    if img and img.has_attr("src"):
        src = img["src"]
        if src.startswith("/"):
            src = "https://ar5iv.org" + src

    cap = caption.get_text(" ", strip=True) if caption else ""

    return f"\n![{cap}]({src})\n"


def html_to_markdown(html):
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
            md.append(parse_figure(tag))
        elif tag.name == "table":
            md.append("\n" + parse_table(tag) + "\n")

    return "\n\n".join(md)


def process_arxiv(doi):
    arxiv_id = doi_to_arxiv_id(doi)
    if not arxiv_id:
        return None

    pdf_bytes = download_arxiv_pdf(arxiv_id)

    pdf_path = None
    if pdf_bytes:
        pdf_path = os.path.join(PDF_DIR, f"{arxiv_id}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

    html = fetch_ar5iv_html(arxiv_id)
    if not html:
        return None

    md = html_to_markdown(html)
    if not md:
        return None

    md_path = os.path.join(MD_DIR, f"{arxiv_id}.md")
    save_text(md, md_path)

    return {"paper_id": doi, "md": md_path}


# PUBMED

def doi_to_pmcid(doi):
    url = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
    params = {"ids": doi, "format": "json"}

    for _ in range(MAX_HTTP_RETRIES):
        try:
            r = requests.get(url, params=params, timeout=30)
            return r.json()["records"][0].get("pmcid")
        except:
            pass

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
            r = requests.get(url, params=params, timeout=60)
            if r.status_code == 200:
                return r.text
        except:
            pass

    return None


def textify(elem):
    if elem is None:
        return ""

    parts = [elem.text or ""]
    for c in elem:
        parts.append(textify(c))
        if c.tail:
            parts.append(c.tail)

    return normalize("".join(parts))


def parse_xml_to_md(xml_text):
    root = ET.fromstring(xml_text)
    article = root.find(".//{*}article")

    if article is None:
        return None

    out = []

    title = article.find(".//{*}article-title")
    if title is not None:
        out.append(f"# {textify(title)}\n")

    body = article.find("{*}body")
    if body is not None:
        for sec in body.findall(".//{*}sec"):
            t = sec.find("{*}title")
            if t is not None:
                out.append(f"\n## {textify(t)}\n")

            for p in sec.findall("{*}p"):
                out.append(textify(p) + "\n")

    return "\n".join(out)


def process_pubmed(doi):
    pmcid = doi_to_pmcid(doi)
    if not pmcid:
        return None

    xml = fetch_pmc_xml(pmcid)
    if not xml:
        return None

    md = parse_xml_to_md(xml)
    if not md:
        return None

    md_path = os.path.join(MD_DIR, f"{pmcid}.md")
    save_text(md, md_path)

    return {"paper_id": doi, "md": md_path}


# MARKDOWN PARSER

def parse_markdown(md_text):
    title = ""
    sections = []
    current = None

    for line in md_text.split("\n"):
        raw = line
        line = line.strip()

        if not line:
            continue

        if line.startswith("# ") and not title:
            title = normalize(line[2:])
            continue

        if re.match(r"^##+\s+", line):
            heading = re.sub(r"^##+\s*", "", line)

            if current:
                current["text"] = normalize(current["text"])
                sections.append(current)

            current = {"heading": heading, "text": ""}
            continue

        if current:
            current["text"] += " " + raw

    if current:
        current["text"] = normalize(current["text"])
        sections.append(current)

    return title, sections


def clean_section_name(name):
    name = re.sub(r"\\[a-zA-Z]+", "", name)
    name = re.sub(r"[{}$]", "", name)
    name = re.sub(r"^[a-zA-Z]?\d+(\.\d+)*[.)]?\s*", "", name)
    name = normalize(name)

    if name:
        name = name[0].upper() + name[1:]

    return name


def clean_sections(sections):
    out = []

    for sec in sections:
        content = normalize(sec["text"])
        if not content or len(content) < 10:
            continue

        out.append({
            "name": clean_section_name(sec["heading"]),
            "content": content
        })

    return out


def make_section_id(name: str) -> str:
    return normalize(name).lower().replace(" ", "_")


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
    

def resolve_doi_to_paper(doi: str) -> dict:
    doi = normalize(doi)

    if not doi:
        return {
            "status": "not_found",
            "message": "No DOI was provided.",
        }

    # Decide which source pipeline to use
    if is_arxiv_doi(doi):
        result = process_arxiv(doi)
        source = "arxiv"
    else:
        result = process_pubmed(doi)
        source = "pubmed"

    if not result:
        return {
            "status": "not_found",
            "message": "We couldnt find a paper for this DOI.",
        }

    md_path = result.get("md")
    if not md_path or not os.path.exists(md_path):
        return {
            "status": "not_found",
            "message": "The paper was found, but no markdown file was produced.",
        }

    md_text = load_text(md_path)

    title, raw_sections = parse_markdown(md_text)
    cleaned = clean_sections(raw_sections)

    available_sections = []
    section_map = {}

    for sec in cleaned:
        section_id = make_section_id(sec["name"])

        available_sections.append({
            "id": section_id,
            "name": sec["name"],
        })

        section_map[section_id] = sec["content"]

    return {
        "status": "success",
        "paper": {
            "doi": doi,
            "title": title or "Untitled paper",
            "source": source,
            "availableSections": available_sections,
        },
        "section_map": section_map,
    }