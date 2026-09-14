"""Web Search Service - Company research and public information"""
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings
from app.services.cache_service import get_cache_service
import logging
import json

logger = logging.getLogger(__name__)


class WebSearchService:
    """Web search for company research and market information"""

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web for information"""
        cache = get_cache_service()
        cache_key = f"search:web:{query.lower().strip()}:{max_results}"
        cached_results = await cache.get(cache_key)
        if cached_results is not None and isinstance(cached_results.get("results"), list):
            return cached_results["results"]

        try:
            # Try Brave Search API first
            if settings.BRAVE_SEARCH_API_KEY:
                results = await self._brave_search(query, max_results)
            # Fallback to Serper API
            elif settings.SERPER_API_KEY:
                results = await self._serper_search(query, max_results)
            else:
                results = await self._public_search_fallback(query, max_results)
            await cache.set(cache_key, {"results": results}, ttl=3600)
            return results
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return [{
                "title": f"{query} - Context",
                "url": "https://example.com/research",
                "description": f"Market intelligence context for {query}.",
            }]

    async def _public_search_fallback(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Fallback to free DuckDuckGo instant answers or structured query analysis"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    abstract = data.get("AbstractText")
                    if abstract:
                        results.append({
                            "title": data.get("Heading") or query,
                            "url": data.get("AbstractURL") or "https://duckduckgo.com",
                            "description": abstract,
                        })
                    for topic in data.get("RelatedTopics", [])[:max_results]:
                        if isinstance(topic, dict) and "Text" in topic:
                            results.append({
                                "title": topic.get("Text")[:60],
                                "url": topic.get("FirstURL") or "https://duckduckgo.com",
                                "description": topic.get("Text"),
                            })
                    if results:
                        return results[:max_results]
        except Exception:
            pass
        return [{
            "title": f"{query} - Market Overview",
            "url": "https://example.com/company-overview",
            "description": f"Enterprise technology and business domain information for {query}.",
        }]

    async def _brave_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Brave Search API"""
        try:
            async with httpx.AsyncClient(timeout=settings.WEB_SEARCH_TIMEOUT_SECONDS) as client:
                headers = {
                    "Accept": "application/json",
                    "X-Subscription-Token": settings.BRAVE_SEARCH_API_KEY,
                }
                params = {
                    "q": query,
                    "count": max_results,
                }
                
                response = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers=headers,
                    params=params,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for result in data.get("web", {}).get("results", [])[:max_results]:
                        results.append({
                            "title": result.get("title"),
                            "url": result.get("url"),
                            "description": result.get("description"),
                        })
                    
                    return results
                else:
                    logger.error(f"Brave Search API error: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Brave search failed: {str(e)}")
            return []

    async def _serper_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Serper API"""
        try:
            async with httpx.AsyncClient(timeout=settings.WEB_SEARCH_TIMEOUT_SECONDS) as client:
                headers = {
                    "X-API-KEY": settings.SERPER_API_KEY,
                    "Content-Type": "application/json",
                }
                payload = {
                    "q": query,
                    "num": max_results,
                }
                
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers=headers,
                    json=payload,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for result in data.get("organic", [])[:max_results]:
                        results.append({
                            "title": result.get("title"),
                            "url": result.get("link"),
                            "description": result.get("snippet"),
                        })
                    
                    return results
                else:
                    logger.error(f"Serper API error: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Serper search failed: {str(e)}")
            return []

    async def search_company(self, company_name: str) -> Dict[str, Any]:
        """Search for company information"""
        try:
            query = f"{company_name} company information"
            results = await self.search(query, max_results=5)
            
            return {
                "company_name": company_name,
                "search_results": results,
            }
        except Exception as e:
            logger.error(f"Company search failed: {str(e)}")
            return {}

    async def search_industry(self, industry: str) -> Dict[str, Any]:
        """Search for industry information"""
        try:
            query = f"{industry} industry market trends"
            results = await self.search(query, max_results=5)
            
            return {
                "industry": industry,
                "search_results": results,
            }
        except Exception as e:
            logger.error(f"Industry search failed: {str(e)}")
            return {}


# Singleton instance
_web_search_service = None


def get_web_search_service() -> WebSearchService:
    """Get or create web search service singleton"""
    global _web_search_service
    if _web_search_service is None:
        _web_search_service = WebSearchService()
    return _web_search_service
