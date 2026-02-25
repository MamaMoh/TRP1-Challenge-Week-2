"""PDF parsing tools for document analysis."""
import re
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Any, List

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


def verify_file_claims(pdf_content: str, repo_files: List[str]) -> Dict[str, bool]:
    """Cross-reference file paths mentioned in PDF with actual repository files.
    
    Args:
        pdf_content: Extracted PDF text content
        repo_files: List of actual file paths in repository
        
    Returns:
        Dictionary mapping mentioned file paths to whether they exist
    """
    mentioned_files = {}
    repo_file_set = set(repo_files)
    
    # Simple heuristic: look for patterns like "src/", "file.py", etc.
    import re
    file_patterns = [
        r'src/[^\s\)]+\.py',
        r'[a-zA-Z_][a-zA-Z0-9_]*\.py',
        r'[a-zA-Z_][a-zA-Z0-9_]*/[^\s\)]+\.py',
    ]
    
    for pattern in file_patterns:
        matches = re.findall(pattern, pdf_content)
        for match in matches:
            key = match.strip().replace("\\", "/").lstrip("./")
            if key and key not in mentioned_files:
                mentioned_files[key] = key in repo_file_set
    
    return mentioned_files
