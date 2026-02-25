"""AST-based code structure verification.

Includes: state models (Pydantic/TypedDict, reducers), graph wiring (edges,
conditional edges, entry point), safe tool checks, and judge structured output.
"""
import ast
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

from src.utils.ast_cache import get_ast_cache

# Expected graph node names for fan-out/fan-in verification (rubric)
EXPECTED_DETECTIVE_NODES = {"repo_investigator", "doc_analyst", "vision_inspector"}
EXPECTED_SYNC_NODE = "evidence_aggregator"
EXPECTED_JUDGE_NODES = {"prosecutor", "defense", "tech_lead"}
EXPECTED_CHIEF_NODE = "chief_justice"
EXPECTED_ENTRY = "start"


def _ast_arg_to_str(arg: ast.AST) -> Optional[str]:
    """Extract string value from AST node (Constant or Name)."""
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value
    if isinstance(arg, ast.Name):
        return arg.id
    return None


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
                    
                # Check for reducers: Annotated[..., operator.add] or operator.ior (AST)
                for node in ast.walk(tree):
                    if isinstance(node, ast.AnnAssign) and node.annotation:
                        ann = node.annotation
                        if isinstance(ann, ast.Subscript):
                            slice_val = ann.slice
                            if isinstance(slice_val, ast.Tuple):
                                elts = slice_val.elts
                                slice_val = elts[1] if len(elts) > 1 else (elts[0] if elts else None)
                            if slice_val and isinstance(slice_val, ast.Attribute):
                                if getattr(slice_val.value, "id", None) == "operator":
                                    if slice_val.attr in ("add", "ior"):
                                        has_reducers = True
                                        break
                            elif slice_val and isinstance(slice_val, ast.Name) and "operator" in content:
                                has_reducers = True
                                break
                
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
        
        # Look for StateGraph, add_edge, add_conditional_edges, set_entry_point
        has_stategraph = False
        has_parallel_edges = False
        has_conditional_edges = False
        edge_count = 0
        source_nodes: Dict[str, int] = {}
        target_nodes: Dict[str, int] = {}
        edges: List[Tuple[str, str]] = []
        conditional_source: Optional[str] = None
        entry_point_node: Optional[str] = None
        has_set_entry_point = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                if attr == "StateGraph":
                    has_stategraph = True
                if attr == "add_edge" and len(node.args) >= 2:
                    edge_count += 1
                    source = _ast_arg_to_str(node.args[0])
                    target = _ast_arg_to_str(node.args[1])
                    if source and target:
                        edges.append((source, target))
                        source_nodes[source] = source_nodes.get(source, 0) + 1
                        target_nodes[target] = target_nodes.get(target, 0) + 1
                if attr == "add_conditional_edges" and len(node.args) >= 1:
                    has_conditional_edges = True
                    conditional_source = _ast_arg_to_str(node.args[0])
                if attr == "set_entry_point" and len(node.args) >= 1:
                    has_set_entry_point = True
                    entry_point_node = _ast_arg_to_str(node.args[0])

        # Verify graph wiring: expected nodes and structure
        all_node_names: Set[str] = set(source_nodes.keys()) | set(target_nodes.keys())
        has_detectives = EXPECTED_DETECTIVE_NODES.issubset(all_node_names)
        has_sync = EXPECTED_SYNC_NODE in all_node_names
        has_judges = EXPECTED_JUDGE_NODES.issubset(all_node_names)
        has_chief = EXPECTED_CHIEF_NODE in all_node_names
        entry_is_start = entry_point_node == EXPECTED_ENTRY
        has_sync_node = has_sync or any(
            "aggregator" in n.lower() or "sync" in n.lower()
            for n in all_node_names
        )

        has_fan_out = any(c > 1 for c in source_nodes.values())
        has_fan_in = any(c > 1 for c in target_nodes.values())
        has_parallel_edges = has_fan_out or has_fan_in

        wiring_ok = (
            has_detectives and has_sync and has_judges and has_chief
            and (has_set_entry_point and entry_is_start)
            and has_conditional_edges
        )
        confidence = (
            0.95 if (has_stategraph and wiring_ok and has_fan_out and has_fan_in)
            else 0.9 if (has_stategraph and has_fan_out and has_fan_in and has_sync_node)
            else 0.5 if has_stategraph else 0.3
        )
        rationale = (
            f"StateGraph: {has_stategraph}, Fan-out: {has_fan_out}, Fan-in: {has_fan_in}, "
            f"Sync: {has_sync_node}, Conditional: {has_conditional_edges}, Entry: {entry_point_node}, "
            f"Edges: {edge_count}, Wiring: detectives={has_detectives} sync={has_sync} judges={has_judges} chief={has_chief}"
        )
        snippet_len = 4000
        graph_structure = content[:snippet_len] if len(content) > snippet_len else content
        return {
            "has_parallel_execution": has_stategraph and has_parallel_edges,
            "has_fan_out": has_fan_out,
            "has_fan_in": has_fan_in,
            "has_conditional_edges": has_conditional_edges,
            "has_sync_node": has_sync_node,
            "graph_structure": graph_structure,
            "file_path": "src/graph.py",
            "rationale": rationale,
            "confidence": confidence,
            "graph_edges": edges,
            "graph_wiring_ok": wiring_ok,
            "entry_point": entry_point_node,
            "has_set_entry_point": has_set_entry_point,
            "conditional_edges_source": conditional_source,
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
                    
                    # Only flag actual os.system(...) calls (AST), not string checks or comments
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Call):
                                if isinstance(node.func, ast.Attribute):
                                    if getattr(node.func.value, "id", None) == "os" and node.func.attr == "system":
                                        has_os_system = True
                                        break
                    except SyntaxError:
                        pass
                    
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

    Uses AST to confirm .with_structured_output() (or bind_tools) is called with
    a schema type (e.g. JudicialOpinion).
    """
    judges_file = os.path.join(repo_path, "src/nodes/judges.py")

    if not os.path.exists(judges_file):
        return {
            "has_structured_output": False,
            "uses_pydantic": False,
            "has_retry": False,
            "file_path": "",
            "rationale": "src/nodes/judges.py not found",
            "confidence": 0.9,
        }

    try:
        with open(judges_file, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content)

        has_structured_output = False
        uses_judicial_opinion_schema = False
        has_retry = "retry" in content.lower() or ("try:" in content and "except" in content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                if attr == "with_structured_output":
                    has_structured_output = True
                    if node.args and isinstance(node.args[0], ast.Name):
                        if node.args[0].id == "JudicialOpinion":
                            uses_judicial_opinion_schema = True
                if attr == "bind_tools" and node.args:
                    has_structured_output = True

        uses_pydantic = uses_judicial_opinion_schema or (
            "JudicialOpinion" in content and "with_structured_output" in content
        )
        rationale = (
            f"Structured output: {has_structured_output}, "
            f"JudicialOpinion schema: {uses_judicial_opinion_schema}, Retry: {has_retry}"
        )
        confidence = (
            0.95 if (has_structured_output and uses_judicial_opinion_schema and has_retry)
            else 0.9 if (has_structured_output and uses_pydantic)
            else 0.5 if has_structured_output else 0.3
        )
        return {
            "has_structured_output": has_structured_output,
            "uses_pydantic": uses_pydantic,
            "has_retry": has_retry,
            "file_path": "src/nodes/judges.py",
            "rationale": rationale,
            "confidence": confidence,
        }
    except (SyntaxError, Exception) as e:
        return {
            "has_structured_output": False,
            "uses_pydantic": False,
            "has_retry": False,
            "file_path": "src/nodes/judges.py",
            "rationale": f"Error reading judges.py: {str(e)}",
            "confidence": 0.1,
        }
