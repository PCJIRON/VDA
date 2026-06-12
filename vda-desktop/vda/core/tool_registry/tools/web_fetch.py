"""Web fetch tool — skeleton for Phase 3.

Fetches content from a URL and returns it as clean markdown.
"""

import logging

from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import register_tool

import httpx
import re
import html as html_lib

logger = logging.getLogger(__name__)


@register_tool("web_fetch")
class WebFetchTool(BaseTool):
    """Fetch content from a URL and return as clean markdown."""

    name = "web_fetch"
    description = "Fetch content from a URL and return as clean markdown"
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to fetch",
            }
        },
        "required": ["url"],
    }

    async def execute(self, **kwargs) -> str:
        """Execute tool.

        Args:
            **kwargs: Must include ``url``.

        Returns:
            URL text content as markdown/text.
        """
        url = kwargs.get("url")
        if not url:
            return "Error: No URL specified"

        logger.info("[%s] Fetching URL: %s", self.name, url)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=15, follow_redirects=True)
                if response.status_code != 200:
                    return f"Error: Fetch returned HTTP {response.status_code}"

                html_text = response.text

                # Strip script and style tags
                html_text = re.sub(r'<script.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
                html_text = re.sub(r'<style.*?</style>', '', html_text, flags=re.DOTALL | re.IGNORECASE)

                # Extract headers and paragraphs
                content_blocks = []
                matches = re.finditer(r'<(h[1-3]|p)[^>]*>(.*?)</\1>', html_text, re.DOTALL | re.IGNORECASE)

                for m in matches:
                    tag = m.group(1).lower()
                    text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
                    text = html_lib.unescape(text)
                    text = re.sub(r'\s+', ' ', text)
                    if not text:
                        continue
                    if tag.startswith('h'):
                        content_blocks.append(f"\n## {text}\n")
                    else:
                        content_blocks.append(text)

                if not content_blocks:
                    # Fallback: strip all html tags and return first few non-empty lines
                    text = re.sub(r'<[^>]+>', '', html_text, flags=re.DOTALL)
                    text = html_lib.unescape(text)
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    return "\n".join(lines[:100])

                return "\n\n".join(content_blocks[:50])
        except Exception as e:
            logger.error("[%s] Fetch error: %s", self.name, e, exc_info=True)
            return f"Error fetching URL: {e}"
