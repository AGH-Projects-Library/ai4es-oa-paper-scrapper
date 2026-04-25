import os
import re
import io
import tarfile
import gzip
import time
import requests
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup


# =========================================================
# CONFIG (adapted from notebooks/to_json.ipynb to backend/data/*)
# =========================================================

BASE = "data"

MD_DIR = os.path.join(BASE, "md")
PDF_DIR = os.path.join(BASE, "pdf")
XML_DIR = os.path.join(BASE, "xml")
TMP_DIR = os.path.join(BASE, "tmp")
META_DIR = os.path.join(BASE, "meta")

for d in [MD_DIR, PDF_DIR, XML_DIR, TMP_DIR, META_DIR]:
    os.makedirs(d, exist_ok=True)

SESSION = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0"}
MAX_HTTP_RETRIES = 5


# =========================================================
# UTILS
# =========================================================

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def save_text(data: str, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def textify(elem) -> str:
    if elem is None:
        return ""

    parts = [elem.text or ""]
    for c in elem:
        parts.append(textify(c))
        if c.tail:
            parts.append(c.tail)

    return normalize("".join(parts))


# =========================================================
# MARKDOWN PARSER (from to_json.ipynb, simplified: ignore tables/images)
# =========================================================

def parse_markdown(md_text: str):
    title = ""
    sections = []
    current = None

    for line in md_text.split("\n"):
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("# ") and not title:
            title = normalize(stripped[2:])
            continue

        if re.match(r"^##+\s+", stripped):
            if current:
                sections.append(current)

            heading = re.sub(r"^##+\s*", "", stripped)
            current = {"heading": heading, "text": ""}
            continue

        if current:
            current["text"] += " " + line

    if current:
        sections.append(current)

    return title, sections


def clean_sections(sections):
    return [s for s in sections if len(normalize(s.get("text", ""))) > 5]


def make_section_id(name: str) -> str:
    return normalize(name).lower().replace(" ", "_")


# =========================================================
# PMC / PubMed Central (subset from to_json.ipynb, images ignored)
# =========================================================

def doi_to_pmcid(doi: str):
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


def fetch_pmc_xml(pmcid: str):
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


def extract_pmc_authors_emails(xml_text: str):
    root = ET.fromstring(xml_text)

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


def parse_pmc_article_to_markdown(xml_text: str):
    root = ET.fromstring(xml_text)
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

    for sec in body.findall(".//{*}sec"):
        sec_title = sec.find("{*}title")
        if sec_title is not None:
            out.append(f"\n## {textify(sec_title)}\n")

        for p in sec.findall("{*}p"):
            txt = textify(p)
            if txt:
                out.append(txt + "\n")

    return "\n".join(out)


def process_pmc(doi: str):
    pmcid = doi_to_pmcid(doi)
    if not pmcid:
        return None

    xml = fetch_pmc_xml(pmcid)
    if not xml:
        return None

    authors, emails = extract_pmc_authors_emails(xml)

    md = parse_pmc_article_to_markdown(xml)
    if not md:
        return None

    md_path = os.path.join(MD_DIR, f"{pmcid}.md")
    save_text(md, md_path)

    return {
        "paper_id": doi,
        "source": "pmc",
        "pmcid": pmcid,
        "md": md_path,
        "authors": authors,
        "emails": emails,
    }


# =========================================================
# arXiv (subset from to_json.ipynb, images ignored)
# =========================================================

def is_arxiv_identifier(text: str) -> bool:
    low = (text or "").lower()
    return "arxiv" in low or re.search(r"\b\d{4}\.\d{4,5}(v\d+)?\b", low) is not None


def doi_to_arxiv_id(doi: str):
    m = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", doi or "", flags=re.I)
    if m:
        return m.group(1)
    return None


def fetch_ar5iv_html(arxiv_id: str):
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


def download_arxiv_source(arxiv_id: str) -> bytes:
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    r = SESSION.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.content


def unpack_archive(content: bytes):
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


def extract_balanced_blocks(text: str, command: str):
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
            results.append(text[brace_start + 1 : end])

    return results


def find_author_files(files: dict):
    author_files = {}
    for filename, tex in files.items():
        blocks = extract_balanced_blocks(tex, "author")
        if blocks:
            author_files[filename] = blocks
    return author_files


def normalize_author_name(name: str) -> str:
    name = (name or "").strip()
    name = re.sub(r"^(?:AND|And|and)\s+", "", name)
    name = re.sub(r"[^A-Za-z.\-'\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" ,;")
    return name


def looks_like_person_name(line: str) -> bool:
    line = (line or "").strip(" ,;")
    if not line or "@" in line:
        return False

    words = line.split()
    if len(words) < 2 or len(words) > 6:
        return False

    valid_words = 0
    for word in words:
        cleaned = re.sub(r"[^A-Za-z.\-']", "", word)
        if cleaned and cleaned[0].isupper():
            valid_words += 1

    return valid_words >= 2 and len(line) <= 60


def clean_single_author_block(block: str):
    text = (block or "").replace("\r", "\n")

    text = text.replace("\\\\", "\n")
    text = re.sub(r"\\and\b|\\And\b|\\AND\b", "\n", text)
    text = re.sub(r"\s+\band\b\s+", "\n", text, flags=re.IGNORECASE)

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\\thanks\s*\{([^{}]|\{[^{}]*\})*\}", "", text)

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\\footnote\s*\{([^{}]|\{[^{}]*\})*\}", "", text)

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

    authors = []
    seen = set()

    for cand in raw_lines:
        cand = normalize_author_name(cand)
        if looks_like_person_name(cand):
            key = cand.lower()
            if key not in seen:
                seen.add(key)
                authors.append(cand)

    return authors


def extract_emails_from_text(tex: str):
    emails = []

    grouped = re.findall(r"\{([^{}]+)\}\\?@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})", tex or "")
    for users, domain in grouped:
        for user in users.split(","):
            user = user.strip().strip("\\")
            if user:
                emails.append(f"{user}@{domain}")

    normal = re.findall(
        r"[A-Za-z0-9._%+\-]+\\?@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
        tex or "",
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


def collect_authors_and_emails(files: dict):
    author_files = find_author_files(files)

    all_authors = []
    all_emails = []

    for filename, author_blocks in author_files.items():
        for block in author_blocks:
            all_authors.extend(clean_single_author_block(block))

        all_emails.extend(extract_emails_from_text(files.get(filename, "")))

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


def parse_html_table(table) -> str:
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
            r = r[: len(rows[0])]
        md.append("| " + " | ".join(r) + " |")

    return "\n".join(md)


def html_to_markdown_arxiv(html: str):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article")

    if not article:
        return None

    md = []

    for tag in article.find_all(["h1", "h2", "h3", "p", "li", "pre", "table"]):
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
        elif tag.name == "table":
            table_md = parse_html_table(tag)
            if table_md:
                md.append("\n" + table_md + "\n")

    return "\n\n".join(md)


def process_arxiv(doi: str):
    arxiv_id = doi_to_arxiv_id(doi)
    if not arxiv_id:
        return None

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
    save_text(md, md_path)

    return {
        "paper_id": doi,
        "source": "arxiv",
        "arxiv_id": arxiv_id,
        "md": md_path,
        "authors": authors,
        "emails": emails,
    }


# =========================================================
# ROUTER + API WRAPPER
# =========================================================

def process_document(doi: str):
    doi = (doi or "").strip()
    if not doi:
        return None

    if is_arxiv_identifier(doi):
        return process_arxiv(doi)

    pmc_result = process_pmc(doi)
    if pmc_result:
        return pmc_result

    return None


def resolve_doi_to_paper(doi: str) -> dict:
    doi = normalize(doi)

    if not doi:
        return {"status": "not_found", "message": "No DOI was provided."}

    doc = process_document(doi)
    if not doc:
        return {"status": "not_found", "message": "We couldn't find a paper for this DOI."}

    md_path = doc.get("md")
    if not md_path or not os.path.exists(md_path):
        return {
            "status": "not_found",
            "message": "The paper was found, but no markdown file was produced.",
        }

    md_text = load_text(md_path)

    title, sections = parse_markdown(md_text)
    sections = clean_sections(sections)

    available_sections = []
    section_map = {}

    for sec in sections:
        name = normalize(sec.get("heading", ""))
        if not name:
            continue

        section_id = make_section_id(name)
        available_sections.append({"id": section_id, "name": name})
        section_map[section_id] = normalize(sec.get("text", ""))

    return {
        "status": "success",
        "paper": {
            "doi": doi,
            "title": title or "Untitled paper",
            "source": doc.get("source") or "unknown",
            "authors": doc.get("authors", []) or [],
            "emails": doc.get("emails", []) or [],
            "availableSections": available_sections,
        },
        "section_map": section_map,
    }