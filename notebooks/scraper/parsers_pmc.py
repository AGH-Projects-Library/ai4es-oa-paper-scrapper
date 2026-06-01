import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple, Any

def normalize(text):
    return re.sub(r"\s+", " ", text or "").strip()

def textify(elem):
    if elem is None:
        return ""

    parts = [elem.text or ""]
    for c in elem:
        parts.append(textify(c))
        if c.tail:
            parts.append(c.tail)

    return normalize("".join(parts))

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


def parse_pmc_article_to_markdown(xml) -> Tuple[Optional[str], List[List[str]]]:
    """
    Build markdown from PMC XML.
    Returns: (markdown_text, section_citations)
    where section_citations is a list of lists of ref_ids, 
    one for each section in the body.
    """
    root = ET.fromstring(xml)
    article = root.find(".//{*}article")

    if article is None:
        return None, []

    out = []
    section_citations = []

    title = article.find(".//{*}article-title")
    if title is not None:
        out.append(f"# {textify(title)}\n")

    body = article.find("{*}body")
    if body is None:
        return "\n".join(out), []

    fig_counter = 0

    for sec in body.findall(".//{*}sec"):
        current_section_citations = []
        sec_title = sec.find("{*}title")
        if sec_title is not None:
            out.append(f"\n## {textify(sec_title)}\n")

        # paragraph text directly under this section
        for p in sec.findall("{*}p"):
            txt = textify(p)
            if txt:
                out.append(txt + "\n")
            
            # Extract citations from this paragraph
            for xref in p.findall(".//{*}xref[@ref-type='bibr']"):
                rid = xref.attrib.get("rid")
                if rid:
                    current_section_citations.append(rid)

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

        section_citations.append(list(set(current_section_citations)))

    return "\n".join(out), section_citations


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

def extract_pmc_references(xml) -> List[Dict[str, Any]]:
    """
    Extract bibliography from PMC XML.
    """
    root = ET.fromstring(xml)
    refs = []
    
    for ref_elem in root.findall(".//{*}ref"):
        ref_id = ref_elem.attrib.get("id")
        if not ref_id:
            continue
            
        mixed_citation = ref_elem.find(".//{*}mixed-citation")
        element_citation = ref_elem.find(".//{*}element-citation")
        citation_elem = element_citation if element_citation is not None else mixed_citation
        
        if citation_elem is None:
            continue
            
        ref_text = textify(citation_elem)
        
        doi = None
        doi_elem = citation_elem.find(".//{*}pub-id[@pub-id-type='doi']")
        if doi_elem is not None:
            doi = doi_elem.text
            
        pmid = None
        pmid_elem = citation_elem.find(".//{*}pub-id[@pub-id-type='pmid']")
        if pmid_elem is not None:
            pmid = pmid_elem.text
            
        title = None
        article_title = citation_elem.find(".//{*}article-title")
        if article_title is not None:
            title = textify(article_title)
            
        year = None
        year_elem = citation_elem.find(".//{*}year")
        if year_elem is not None:
            year = year_elem.text
            
        refs.append({
            "ref_id": ref_id,
            "text": ref_text,
            "doi": doi,
            "pmid": pmid,
            "title": title,
            "year": year
        })
        
    return refs

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
