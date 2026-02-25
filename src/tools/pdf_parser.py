"""PDF parsing tools for document analysis.

Includes semantic chunking (by section/paragraph), query APIs to find relevant
chunks by keywords or overlap scoring, and cross-reference verification.
"""
import re
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Try to import DocumentConverter with fallback
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    try:
        from docling import DocumentConverter
        DOCLING_AVAILABLE = True
    except ImportError:
        DOCLING_AVAILABLE = False
        DocumentConverter = None


def is_pdf_url(value: str) -> bool:
    """Return True if value looks like an HTTP(S) URL (for PDF)."""
    return value.strip().startswith(("http://", "https://"))


# Google Drive share URL: .../file/d/FILE_ID/view... or .../open?id=FILE_ID
_GD_FILE_ID_RE = re.compile(
    r"drive\.google\.com/(?:file/d/|open\?id=)([a-zA-Z0-9_-]+)"
)


def _normalize_download_url(url: str) -> str:
    """Convert Google Drive share URLs to direct download URL. Other URLs unchanged."""
    url = url.strip()
    match = _GD_FILE_ID_RE.search(url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


def download_pdf_from_url(url: str, dest_dir: str = None) -> str:
    """Download a PDF from URL to a local file.

    Supports direct PDF URLs and Google Drive share links (converted to direct download).

    Args:
        url: HTTP(S) URL to the PDF, or Google Drive share link.
        dest_dir: Directory to save the file (default: tempfile.gettempdir()).

    Returns:
        Absolute path to the downloaded PDF file.

    Raises:
        ValueError: If URL is not http(s).
        RuntimeError: If download fails or response is not a PDF.
    """
    if not is_pdf_url(url):
        raise ValueError(f"Not an HTTP(S) URL: {url}")

    url = _normalize_download_url(url)

    dest_dir = dest_dir or tempfile.gettempdir()
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    safe_name = "downloaded_report.pdf"
    dest_path = Path(dest_dir) / safe_name

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
            content_type = resp.headers.get("Content-Type", "").lower()
            is_pdf_content = data.startswith(b"%PDF")
            if is_pdf_content:
                pass
            elif "pdf" in content_type or "octet-stream" in content_type:
                pass
            elif "text/html" in content_type or (not is_pdf_content and len(data) > 0):
                raise RuntimeError(
                    "URL did not return a PDF (got HTML or other content). "
                    "For Google Drive: use a link shared with 'Anyone with the link', or try the direct download format: "
                    "https://drive.google.com/uc?export=download&id=FILE_ID"
                )
            else:
                raise RuntimeError(f"URL did not return a PDF (Content-Type: {content_type})")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"PDF download failed: HTTP {e.code} {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"PDF download failed: {e.reason}") from e

    dest_path.write_bytes(data)
    return str(dest_path.resolve())


def parse_pdf(pdf_path: str) -> str:
    """Parse PDF and extract text content using Docling.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text content as string
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        RuntimeError: If PDF parsing fails
    """
    pdf_file = Path(pdf_path)
    
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Try Docling first (if available and working)
    if DOCLING_AVAILABLE and DocumentConverter:
        try:
            converter = DocumentConverter()
            doc = converter.convert(str(pdf_file))
            # Handle different docling API versions
            if hasattr(doc, 'document'):
                return doc.document.export_to_markdown()
            elif hasattr(doc, 'export_to_markdown'):
                return doc.export_to_markdown()
            else:
                # Fallback: try to get text content
                return str(doc)
        except (OSError, ImportError, Exception) as e:
            # If docling fails (e.g., Windows security policy blocking pypdfium2),
            # fall back to pypdf
            pass
    
    # Fallback to pypdf (lighter weight, more reliable, works on Windows)
    try:
        import pypdf
        with open(pdf_file, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text_content.append(page.extract_text())
                except Exception as page_error:
                    # Skip pages that fail to extract
                    text_content.append(f"[Page {page_num + 1}: Extraction failed]")
            return '\n'.join(text_content)
    except ImportError:
        # If pypdf is not available, try PyPDF2
        try:
            import PyPDF2
            with open(pdf_file, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = []
                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())
                return '\n'.join(text_content)
        except ImportError:
            raise RuntimeError(
                "PDF parsing failed: Neither docling, pypdf, nor PyPDF2 are available. "
                "Please install one of: pypdf (recommended), PyPDF2, or fix docling installation"
            ) from None
    except Exception as e:
        raise RuntimeError(f"PDF parsing failed: {str(e)}") from e


def extract_keywords(pdf_content: str, keywords: List[str]) -> Dict[str, List[str]]:
    """Extract sentences containing specific keywords from PDF content.
    
    Args:
        pdf_content: Extracted PDF text content
        keywords: List of keywords to search for
        
    Returns:
        Dictionary mapping keyword to list of sentences containing it
    """
    results = {keyword: [] for keyword in keywords}
    sentences = pdf_content.split('.')
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        for keyword in keywords:
            if keyword.lower() in sentence_lower:
                results[keyword].append(sentence.strip())
    
    return results


def _normalize_path_for_match(p: str) -> str:
    """Normalize path for case-insensitive and slash-agnostic comparison."""
    return p.strip().replace("\\", "/").lstrip("./").lower()


def verify_file_claims(pdf_content: str, repo_files: List[str]) -> Dict[str, bool]:
    """Cross-reference file paths mentioned in PDF with actual repository files.

    Uses case-insensitive and slash-normalized matching so e.g. src/State.py
    matches repo file src/state.py. Only counts paths that look like project paths
    (src/, rubric/, docs/, tests/, main.py) to reduce false positives from generic .py mentions.
    """
    mentioned_files: Dict[str, bool] = {}
    repo_normalized = {_normalize_path_for_match(f): f for f in repo_files}

    # Prefer project-relevant path patterns to avoid matching random "foo.py" in text
    file_patterns = [
        r"src/[^\s\)\]\"]+\.py",
        r"rubric/[^\s\)\]\"]+\.json",
        r"docs/[^\s\)\]\"]+",
        r"tests/[^\s\)\]\"]+\.py",
        r"main\.py",
    ]

    for pattern in file_patterns:
        for match in re.findall(pattern, pdf_content):
            key = match.strip().replace("\\", "/").lstrip("./")
            if not key or key in mentioned_files:
                continue
            key_norm = _normalize_path_for_match(key)
            mentioned_files[key] = key_norm in repo_normalized

    return mentioned_files


# --- Semantic chunking and query APIs ---

# Section headers: markdown-style ## or lines that look like titles (short, no trailing period)
_SECTION_HEADER_RE = re.compile(r"^(#{1,6}\s+.+)$|^([A-Z][^\n.]{2,60})$", re.MULTILINE)


def chunk_pdf_semantic(
    pdf_content: str,
    max_chunk_chars: int = 1200,
    overlap_chars: int = 100,
) -> List[Dict[str, Any]]:
    """Split PDF text into semantic chunks (by section/paragraph) for retrieval.

    Chunks respect section boundaries when possible (headers, double newlines).
    Each chunk has 'text', 'start', 'end' (byte offsets), and optional 'section' title.

    Args:
        pdf_content: Full extracted PDF text.
        max_chunk_chars: Soft max length per chunk.
        overlap_chars: Overlap between consecutive chunks to avoid breaking phrases.

    Returns:
        List of dicts: {"text": str, "start": int, "end": int, "section": str or None}.
    """
    if not pdf_content or not pdf_content.strip():
        return []

    chunks: List[Dict[str, Any]] = []
    # Split into paragraphs (double newline or section header)
    parts: List[Tuple[int, str, Optional[str]]] = []  # (start, text, section_header)
    current_start = 0
    section_header: Optional[str] = None
    pos = 0
    normalized = pdf_content.replace("\r\n", "\n").replace("\r", "\n")

    for m in _SECTION_HEADER_RE.finditer(normalized):
        if m.start() > pos:
            paragraph = normalized[pos : m.start()].strip()
            if paragraph:
                parts.append((pos, paragraph, section_header))
        section_header = (m.group(1) or m.group(2) or "").strip() or None
        pos = m.start()

    if pos < len(normalized):
        paragraph = normalized[pos:].strip()
        if paragraph:
            parts.append((pos, paragraph, section_header))

    # If no headers found, split by double newline only
    if not parts:
        for i, block in enumerate(re.split(r"\n\s*\n", normalized)):
            block = block.strip()
            if not block:
                continue
            start = normalized.find(block, 0)
            if start < 0:
                start = sum(len(p[1]) for p in parts)
            parts.append((start, block, None))

    # Build chunks within max_chunk_chars, keeping section context
    current_text: List[str] = []
    current_len = 0
    chunk_start = 0
    chunk_section: Optional[str] = None
    for start, text, section in parts:
        if current_len + len(text) + 1 <= max_chunk_chars:
            if not current_text:
                chunk_start = start
                chunk_section = section
            current_text.append(text)
            current_len += len(text) + 1
        else:
            if current_text:
                full = " \n".join(current_text)
                chunks.append({
                    "text": full,
                    "start": chunk_start,
                    "end": chunk_start + len(full),
                    "section": chunk_section,
                })
            # Start new chunk; optionally carry over overlap
            overlap = ""
            if overlap_chars > 0 and current_text:
                overlap = " \n".join(current_text)[-overlap_chars:]
            current_text = [overlap + text] if overlap else [text]
            current_len = len(current_text[0])
            chunk_start = start
            chunk_section = section
    if current_text:
        full = " \n".join(current_text)
        chunks.append({
            "text": full,
            "start": chunk_start,
            "end": chunk_start + len(full),
            "section": chunk_section,
        })
    return chunks


def _chunk_score(chunk_text: str, query_terms: List[str]) -> float:
    """Score a chunk by keyword overlap (case-insensitive)."""
    lower = chunk_text.lower()
    return sum(1 for t in query_terms if t.lower() in lower)


def query_pdf_chunks(
    chunks: List[Dict[str, Any]],
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Return the top-k chunks most relevant to a query (keyword overlap).

    Query is split into words; chunks are scored by how many query terms they contain.
    Ties are broken by chunk length (prefer shorter, more focused chunks).

    Args:
        chunks: Output of chunk_pdf_semantic().
        query: Search phrase or space-separated keywords.
        top_k: Max number of chunks to return.

    Returns:
        List of chunk dicts with an added "score" field, sorted by relevance.
    """
    if not chunks or not query.strip():
        return []

    terms = [t.strip() for t in query.split() if t.strip()]
    if not terms:
        return chunks[:top_k]

    scored: List[Dict[str, Any]] = []
    for c in chunks:
        text = c.get("text", "")
        score = _chunk_score(text, terms)
        scored.append({**c, "score": score})

    scored.sort(key=lambda x: (-x["score"], len(x.get("text", ""))))
    return [c for c in scored if c["score"] > 0][:top_k]


def get_pdf_chunks_for_keywords(
    pdf_content: str,
    keywords: List[str],
    max_chunk_chars: int = 1200,
    top_k_per_keyword: int = 2,
) -> Dict[str, List[Dict[str, Any]]]:
    """Chunk the PDF semantically and return relevant chunks per keyword.

    Convenience API: chunk once, then for each keyword run a query and store
    the top chunks. Useful for rubric-driven extraction (e.g. theoretical depth).

    Args:
        pdf_content: Full PDF text.
        keywords: List of terms to search for.
        max_chunk_chars: Passed to chunk_pdf_semantic.
        top_k_per_keyword: Max chunks to return per keyword.

    Returns:
        Dict mapping each keyword to a list of chunk dicts (with "score").
    """
    chunks = chunk_pdf_semantic(pdf_content, max_chunk_chars=max_chunk_chars)
    result: Dict[str, List[Dict[str, Any]]] = {}
    for kw in keywords:
        result[kw] = query_pdf_chunks(chunks, kw, top_k=top_k_per_keyword)
    return result
