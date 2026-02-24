"""PDF parsing tools for document analysis."""
from pathlib import Path
from typing import Dict, Any, List
from docling import DocumentConverter


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
    
    try:
        converter = DocumentConverter()
        doc = converter.convert(str(pdf_file))
        return doc.document.export_to_markdown()
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
            if match not in mentioned_files:
                mentioned_files[match] = match in repo_file_set
    
    return mentioned_files
