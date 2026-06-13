import httpx
from common.logger import logger
from orchestrator.tools.constants import MAX_LEN , MAX_KEEP

def fetch_url(url: str) -> dict:
    """Fetch raw content from a URL — for pulling docs, APIs, raw files."""
    logger.info("fetch_url: %s", url)
    try:
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        content = resp.text
        
        if len(content) > MAX_LEN:
            content = content[:MAX_KEEP] + "\n...[truncated]...\n" + content[-MAX_KEEP:]
            
        return {
                    "url":         url,
                    "status_code": resp.status_code,
                    "content":     content,
                    "success":     resp.status_code == 200,
                }
        
    except Exception as e:
        logger.error("fetch_url error: %s", e)
        return {"url": url, "content": "", "error": str(e), "success": False}