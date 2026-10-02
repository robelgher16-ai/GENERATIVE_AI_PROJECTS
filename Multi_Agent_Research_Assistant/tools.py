# =====================================================
# IMPORTS
# =====================================================

from langchain.tools import tool
from bs4 import BeautifulSoup
import requests

from ddgs import DDGS


# =====================================================
# TOOL 1 : WEB SEARCH
# Purpose : Search the web for research sources
# =====================================================

@tool
def web_search(query: str) -> str:
    """
    Search the web and return titles, URLs, and snippets.
    """

    try:

        results = []

        with DDGS() as ddgs:

            search_results = ddgs.text(
                query,
                max_results=5
            )

            for item in search_results:

                results.append(
                    f"""Title: {item.get('title')}
URL: {item.get('href')}
Snippet: {item.get('body')}
"""
                )

        if not results:
            return "No search results found."

        return "\n------------------------\n".join(results)

    except Exception as e:

        return f"Search failed: {e}"


# =====================================================
# TOOL 2 : SCRAPE URL
# Purpose : Extract readable text from a webpage
# =====================================================

@tool
def scrape_url(url: str) -> str:
    """
    Scrape a webpage and return its readable text content.
    """

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=30
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Remove unnecessary webpage elements
        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header"
        ]):
            tag.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True
        )

        return text[:4000]

    except Exception as e:

        return f"Scraping failed: {e}"