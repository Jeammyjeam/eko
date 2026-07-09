import sys
import json
import time
from ddgs import DDGS

def web_search(query, max_results=5, max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results, timeout=20))
                return results
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Web search failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Web search failed after {max_retries} attempts: {e}")
                raise # Re-raise the last exception after exhausting retries
    return [] # Should not be reached if an exception is re-raised, but as a fallback

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "CORTEX AI"
    try:
        results = web_search(query)
        if results:
            for r in results:
                print(f"[{r.get('title')}]")
                print(f"  {r.get('href')}")
                print(f"  {r.get('body','')[:150]}")
                print()
        else:
            print("No results found.")
    except Exception as e:
        print(f"An unrecoverable error occurred during web search: {e}")
        sys.exit(1)