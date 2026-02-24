"""AST parsing cache for performance optimization."""
import ast
import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Optional


class ASTCache:
    """Cache for parsed AST trees to avoid re-parsing unchanged files."""
    
    def __init__(self):
        """Initialize the cache."""
        self._cache: Dict[str, ast.AST] = {}
        self._file_hashes: Dict[str, str] = {}
    
    def _get_file_hash(self, file_path: str) -> str:
        """Get hash of file contents for cache invalidation.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash of file contents
        """
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            return hashlib.sha256(content).hexdigest()
        except Exception:
            return ""
    
    def get_ast(self, file_path: str) -> Optional[ast.AST]:
        """Get cached AST or parse and cache.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Parsed AST tree or None if parsing fails
        """
        if not Path(file_path).exists():
            return None
        
        current_hash = self._get_file_hash(file_path)
        
        # Check if file has changed
        if file_path in self._file_hashes:
            if self._file_hashes[file_path] == current_hash:
                # File unchanged, return cached AST
                return self._cache.get(file_path)
        
        # Parse and cache
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            tree = ast.parse(content)
            self._cache[file_path] = tree
            self._file_hashes[file_path] = current_hash
            return tree
        except SyntaxError:
            return None
        except Exception:
            return None
    
    def clear(self):
        """Clear the cache."""
        self._cache.clear()
        self._file_hashes.clear()


# Global cache instance
_global_cache = ASTCache()


def get_ast_cache() -> ASTCache:
    """Get the global AST cache instance."""
    return _global_cache
