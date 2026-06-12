"""Web search tool — skeleton for Phase 3.

Searches the web via configured search API and returns structured results.
"""

import logging

from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import register_tool

import httpx
import re
import urllib.parse

logger = logging.getLogger(__name__)


@register_tool("web_search")
class WebSearchTool(BaseTool):
    """Search the web for a query and return structured results."""

    name = "web_search"
    description = "Search the web for a query and return structured results"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query",
            }
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs) -> str:
        """Execute tool.

        Args:
            **kwargs: Must include ``query``.

        Returns:
            Search results as formatted string.
        """
        query = kwargs.get("query")
        if not query:
            return "Error: No query specified"

        logger.info("[%s] Searching web for: %s", self.name, query)
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        data = {"q": query}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data, headers=headers, timeout=15)
                if response.status_code != 200:
                    return f"Error: Search returned HTTP {response.status_code}"

                html = response.text
                results = []

                # Find result title links and snippet blocks
                pattern = (
                    r'<h2 class="result__title">.*?<a class="result__a" href="(?P<url>[^"]+)"'
                    r'[^>]*>(?P<title>.*?)</a>.*?<a class="result__snippet"[^>]*>(?P<snippet>.*?)</a>'
                )
                matches = re.finditer(pattern, html, re.DOTALL)

                for m in matches:
                    title = re.sub(r'<[^>]+>', '', m.group('title')).strip()
                    url_match = m.group('url')
                    if "/l/?uddg=" in url_match:
                        parsed = urllib.parse.urlparse(url_match)
                        qs = urllib.parse.parse_qs(parsed.query)
                        real_url = qs.get("uddg", [url_match])[0]
                    else:
                        real_url = url_match

                    snippet = re.sub(r'<[^>]+>', '', m.group('snippet')).strip()
                    results.append(f"Title: {title}\nURL: {real_url}\nSnippet: {snippet}\n")
                    if len(results) >= 5:
                        break

                if not results:
                    # Backup regex for snippets
                    snippets_backup = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
                    if snippets_backup:
                        for i, s in enumerate(snippets_backup[:5]):
                            text = re.sub(r'<[^>]+>', '', s).strip()
                            results.append(f"Result {i+1}: {text}")
                    else:
                        return "No results found. (The HTML structure of search provider may have changed)"

                return "\n".join(results)
        except Exception as e:
            logger.error("[%s] Search error: %s", self.name, e, exc_info=True)
            return f"Error during web search: {e}"
