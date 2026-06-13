from pathlib import Path
from common.logger import logger
from orchestrator.tools.constants import AGENT_WORKSPACE
from orchestrator.tools.constants import MAX_LEN , MAX_KEEP 

WORKSPACE       = Path(AGENT_WORKSPACE)
WORKSPACE.mkdir(parents=True, exist_ok=True)


def _safe_path(path: str) -> Path:
    """Resolve path, allow absolute or relative to workspace."""
    p = Path(path)
    if not p.is_absolute():
        p = WORKSPACE / p
    return p

def read_file(path: str) -> dict:
    p = _safe_path(path)
    
    try:
        content = p.read_text(encoding="utf-8")
        
        if len(content) > MAX_LEN:
            content = content[:MAX_KEEP] + "\n...[truncated]...\n" + content[-MAX_KEEP:]
            
        logger.info("read_file: %s (%d chars)", p, len(content))
        
        return {"path": str(p), "content": content, "success": True}
    
    except Exception as e:
        return {"path": str(p), "content": "", "error": str(e), "success": False}

def write_file(path: str, content: str) -> dict:
    p = _safe_path(path)
    
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        
        logger.info("write_file: %s (%d chars)", p, len(content))
        
        return {"path": str(p), "success": True}
    
    except Exception as e:
        return {"path": str(p), "error": str(e), "success": False}

def list_dir(path: str = ".") -> dict:
    p = _safe_path(path)
    
    try:
        entries = []
        for entry in sorted(p.iterdir()):
            entries.append({
                                "name": entry.name,
                                "type": "dir" if entry.is_dir() else "file",
                                "size": entry.stat().st_size if entry.is_file() else None,
                            }
                           )
        return {"path": str(p), "entries": entries, "success": True}
    
    except Exception as e:
        return {"path": str(p), "entries": [], "error": str(e), "success": False}

def delete_file(path: str) -> dict:
    p = _safe_path(path)
    
    try:
        p.unlink()
        return {"path": str(p), "success": True}
    
    except Exception as e:
        return {"path": str(p), "error": str(e), "success": False}