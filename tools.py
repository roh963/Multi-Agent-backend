from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from rich import print
from tavily import TavilyClient
import os
from dotenv import load_dotenv  
load_dotenv()


tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool("web_search", return_direct=True)
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic. Return Titles , Urls and Snippets"""
    try:
        result = tavily.search(query=query, max_results=5)
        output = []
        for r in result['results']:
            output.append(f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n\n")
        return "\n--------\n".join(output)
    except Exception as e:
        return f"Error during web search: {str(e)}"


# print(web_search.invoke("What is the current war situation?"))

@tool("scrape_url", return_direct=True)
def scrape_url(url: str) -> str:
    """Scrape and clean the content of a webpage given its URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        return f"Error during web scraping: {str(e)}"


# print(scrape_url.invoke("https://www.bbc.com/news/world-europe-66707497"))
