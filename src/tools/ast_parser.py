"""AST-based code structure verification."""
import ast
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.utils.ast_cache import get_ast_cache


def verify_state_models(repo_path: str) -> Dict[str, Any]:
    """Use AST to verify Pydantic state models exist.
    
    Args:
        repo_path: Path to repository root
        
    Returns:
        Dictionary with has_pydantic_state, code_snippet, file_path, rationale, confidence
    """
    state_files = ["src/state.py", "src/graph.py"]
    
    # Use AST cache for performance
    cache = get_ast_cache()
    
    for rel_path in state_files:
        full_path = os.path.join(repo_path, rel_path)
        if os.path.exists(full_path):
            try:
                # Try to get from cache first
                tree = cache.get_ast(full_path)
                if tree is None:
                    # Fallback to direct parsing if cache fails
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    tree = ast.parse(content)
                else:
                    # Read content for snippet extraction
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                
                # Look for BaseModel or TypedDict
                has_pydantic = False
                has_typeddict = False
                has_reducers = False
                has_evidence_model = False
                has_opinion_model = False
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check for BaseModel inheritance
                        for base in node.bases:
                            if isinstance(base, ast.Name) and base.id == "BaseModel":
                                has_pydantic = True
                            elif isinstance(base, ast.Name) and base.id == "TypedDict":
                                has_typeddict = True
                            elif isinstance(base, ast.Attribute):
                                if base.attr == "BaseModel" or base.attr == "TypedDict":
                                    has_pydantic = True
                                    has_typeddict = True
                        
                        # Check for Evidence and JudicialOpinion models
                        if node.name == "Evidence":
                            has_evidence_model = True
                        if node.name == "JudicialOpinion":
                            has_opinion_model = True
                    
                    # Check for reducers (operator.add, operator.ior)
                    if isinstance(node, ast.AnnAssign):
                        if isinstance(node.annotation, ast.Subscript):
                            if isinstance(node.annotation.slice, ast.Name):
                                if "operator" in content and ("add" in content or "ior" in content):
                                    has_reducers = True
                
                if (has_pydantic or has_typeddict) and has_evidence_model and has_opinion_model:
                    # Extract relevant code snippet
                    code_snippet = content[:1000] if len(content) > 1000 else content
                    
                    rationale = f"Found Pydantic BaseModel or TypedDict in {rel_path}"
                    if has_reducers:
                        rationale += " with state reducers (operator.add/ior)"
                    
                    return {
                        "has_pydantic_state": True,
                        "has_reducers": has_reducers,
                        "has_evidence_model": has_evidence_model,
                        "has_opinion_model": has_opinion_model,
                        "code_snippet": code_snippet,
                        "file_path": rel_path,
                        "rationale": rationale,
                        "confidence": 0.9 if has_reducers else 0.7
                    }
            except SyntaxError as e:
                return {
                    "has_pydantic_state": False,
                    "has_reducers": False,
                    "code_snippet": "",
                    "file_path": rel_path,
                    "rationale": f"Syntax error in {rel_path}: {str(e)}",
                    "confidence": 0.1
                }
            except Exception as e:
                continue
    
    return {
        "has_pydantic_state": False,
        "has_reducers": False,
        "code_snippet": "",
        "file_path": "",
        "rationale": "No Pydantic state models found in src/state.py or src/graph.py",
        "confidence": 0.8
    }


def analyze_graph_structure(repo_path: str) -> Dict[str, Any]:
    """Analyze LangGraph structure for parallel execution.
    
    Args:
        repo_path: Path to repository root
        
    Returns:
        Dictionary with has_parallel_execution, graph_structure, file_path, rationale, confidence
    """
    graph_file = os.path.join(repo_path, "src/graph.py")
    
    if not os.path.exists(graph_file):
        return {
            "has_parallel_execution": False,
            "has_fan_out": False,
            "has_fan_in": False,
            "has_conditional_edges": False,
            "graph_structure": "",
            "file_path": "",
            "rationale": "src/graph.py not found",
            "confidence": 0.9
        }
    
    # Use AST cache for performance
    cache = get_ast_cache()
    
    try:
        # Try to get from cache first
        tree = cache.get_ast(graph_file)
        if tree is None:
            # Fallback to direct parsing
            with open(graph_file, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
        else:
            # Read content for structure extraction
            with open(graph_file, "r", encoding="utf-8") as f:
                content = f.read()
        
        # Look for StateGraph instantiation
        has_stategraph = False
        has_parallel_edges = False
        has_conditional_edges = False
        edge_count = 0
        source_nodes = {}
        target_nodes = {}
        
        for node in ast.walk(tree):
            # Check for StateGraph
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "StateGraph":
                        has_stategraph = True
                    
                    # Count add_edge calls and track sources/targets
                    if node.func.attr == "add_edge":
                        edge_count += 1
                        if len(node.args) >= 2:
                            source = None
                            target = None
                            if isinstance(node.args[0], ast.Constant):
                                source = node.args[0].value
                            elif isinstance(node.args[0], ast.Name):
                                source = node.args[0].id
                            
                            if isinstance(node.args[1], ast.Constant):
                                target = node.args[1].value
                            elif isinstance(node.args[1], ast.Name):
                                target = node.args[1].id
                            
                            if source:
                                if source not in source_nodes:
                                    source_nodes[source] = 0
                                source_nodes[source] += 1
                            
                            if target:
                                if target not in target_nodes:
                                    target_nodes[target] = 0
                                target_nodes[target] += 1
                    
                    # Check for conditional edges
                    if node.func.attr == "add_conditional_edges":
                        has_conditional_edges = True
        
        # Check if any source node has multiple edges (fan-out)
        has_fan_out = any(count > 1 for count in source_nodes.values())
        # Check if any target node has multiple incoming edges (fan-in)
        has_fan_in = any(count > 1 for count in target_nodes.values())
        has_parallel_edges = has_fan_out or has_fan_in
        
        # Check for evidence aggregator or synchronization node
        has_sync_node = any(
            "aggregator" in node.lower() or "sync" in node.lower() or "collect" in node.lower()
            for node in list(source_nodes.keys()) + list(target_nodes.keys())
        )
        
        confidence = 0.9 if (has_stategraph and has_fan_out and has_fan_in and has_sync_node) else 0.5 if has_stategraph else 0.3
        
        rationale = (
            f"StateGraph: {has_stategraph}, Fan-out: {has_fan_out}, Fan-in: {has_fan_in}, "
            f"Sync node: {has_sync_node}, Conditional edges: {has_conditional_edges}, "
            f"Total edges: {edge_count}"
        )
        
        return {
            "has_parallel_execution": has_stategraph and has_parallel_edges,
            "has_fan_out": has_fan_out,
            "has_fan_in": has_fan_in,
            "has_conditional_edges": has_conditional_edges,
            "has_sync_node": has_sync_node,
            "graph_structure": content[:1500] if len(content) > 1500 else content,
            "file_path": "src/graph.py",
            "rationale": rationale,
            "confidence": confidence
        }
    except SyntaxError as e:
        return {
            "has_parallel_execution": False,
            "has_fan_out": False,
            "has_fan_in": False,
            "has_conditional_edges": False,
            "graph_structure": "",
            "file_path": "src/graph.py",
            "rationale": f"Syntax error in graph.py: {str(e)}",
            "confidence": 0.1
        }
    except Exception as e:
        return {
            "has_parallel_execution": False,
            "has_fan_out": False,
            "has_fan_in": False,
            "has_conditional_edges": False,
            "graph_structure": "",
            "file_path": "src/graph.py",
            "rationale": f"AST analysis error: {str(e)}",
            "confidence": 0.1
        }


def verify_safe_tool_engineering(repo_path: str) -> Dict[str, Any]:
    """Verify safe tool engineering practices.
    
    Args:
        repo_path: Path to repository root
        
    Returns:
        Dictionary with is_safe, uses_sandboxing, uses_subprocess, has_os_system, file_path, rationale, confidence
    """
    tools_dir = os.path.join(repo_path, "src/tools")
    
    if not os.path.exists(tools_dir):
        return {
            "is_safe": False,
            "uses_sandboxing": False,
            "uses_subprocess": False,
            "has_os_system": False,
            "file_path": "",
            "rationale": "src/tools/ directory not found",
            "confidence": 0.9
        }
    
    uses_sandboxing = False
    uses_subprocess = False
    has_os_system = False
    has_error_handling = False
    tool_files = []
    
    for root, dirs, files in os.walk(tools_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                tool_files.append(file_path)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Check for sandboxing
                    if "tempfile" in content or "TemporaryDirectory" in content:
                        uses_sandboxing = True
                    
                    # Check for subprocess usage
                    if "subprocess" in content and "subprocess.run" in content:
                        uses_subprocess = True
                    
                    # Check for dangerous os.system
                    if "os.system" in content:
                        has_os_system = True
                    
                    # Check for error handling
                    if "try:" in content and "except" in content:
                        has_error_handling = True
                        
                except Exception:
                    continue
    
    is_safe = uses_sandboxing and uses_subprocess and not has_os_system and has_error_handling
    
    rationale = (
        f"Sandboxing: {uses_sandboxing}, Subprocess: {uses_subprocess}, "
        f"os.system: {has_os_system}, Error handling: {has_error_handling}"
    )
    
    confidence = 0.9 if is_safe else 0.5 if (uses_sandboxing or uses_subprocess) else 0.3
    
    return {
        "is_safe": is_safe,
        "uses_sandboxing": uses_sandboxing,
        "uses_subprocess": uses_subprocess,
        "has_os_system": has_os_system,
        "has_error_handling": has_error_handling,
        "file_path": "src/tools/",
        "rationale": rationale,
        "confidence": confidence
    }


def verify_structured_output(repo_path: str) -> Dict[str, Any]:
    """Verify structured output enforcement in judge nodes.
    
    Args:
        repo_path: Path to repository root
        
    Returns:
        Dictionary with has_structured_output, uses_pydantic, has_retry, file_path, rationale, confidence
    """
    judges_file = os.path.join(repo_path, "src/nodes/judges.py")
    
    if not os.path.exists(judges_file):
        return {
            "has_structured_output": False,
            "uses_pydantic": False,
            "has_retry": False,
            "file_path": "",
            "rationale": "src/nodes/judges.py not found",
            "confidence": 0.9
        }
    
    try:
        with open(judges_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        has_structured_output = (
            "with_structured_output" in content or
            "bind_tools" in content or
            "structured_output" in content
        )
        
        uses_pydantic = "JudicialOpinion" in content and "Pydantic" in content
        
        has_retry = (
            "retry" in content.lower() or
            "try:" in content and "except" in content
        )
        
        rationale = (
            f"Structured output: {has_structured_output}, "
            f"Pydantic schema: {uses_pydantic}, "
            f"Retry logic: {has_retry}"
        )
        
        confidence = 0.9 if (has_structured_output and uses_pydantic) else 0.5 if has_structured_output else 0.3
        
        return {
            "has_structured_output": has_structured_output,
            "uses_pydantic": uses_pydantic,
            "has_retry": has_retry,
            "file_path": "src/nodes/judges.py",
            "rationale": rationale,
            "confidence": confidence
        }
    except Exception as e:
        return {
            "has_structured_output": False,
            "uses_pydantic": False,
            "has_retry": False,
            "file_path": "src/nodes/judges.py",
            "rationale": f"Error reading judges.py: {str(e)}",
            "confidence": 0.1
        }
