import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def scrape_facebook_login_tokens(session=None, login_url="https://www.facebook.com/login"):
    """
    Scrape all hidden input tokens from Facebook login page.
    Returns a dictionary of token_name: token_value.
    Accepts an optional requests.Session for cookie persistence.
    """
    if session is None:
        session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = session.get(login_url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the login form (handle both classic and mobile)
    form = None
    for f in soup.find_all("form"):
        action = f.get("action", "")
        if "login" in action or "login" in f.get("id", "") or "login" in f.get("name", ""):
            form = f
            break
    if not form:
        # fallback: pick the first form
        form = soup.find("form")
    if not form:
        raise RuntimeError("No form found on Facebook login page.")

    # Extract all input fields (including hidden)
    tokens = {}
    for inp in form.find_all("input"):
        name = inp.get("name")
        value = inp.get("value", "")
        if name:
            tokens[name] = value

    # Optionally, extract action URL for POST
    action_url = form.get("action")
    if action_url and not action_url.startswith("http"):
        # Relative URL, join with base
        action_url = urljoin(login_url, action_url)
    elif not action_url:
        action_url = login_url

    return {
        "tokens": tokens,
        "action_url": action_url,
        "cookies": session.cookies.get_dict(),
        "raw_html": resp.text,  # for debugging
    }

# Example usage:
if __name__ == "__main__":
    result = scrape_facebook_login_tokens()
    print("Action URL:", result["action_url"])
    print("Tokens:")
    for k, v in result["tokens"].items():
        print(f"  {k}: {v}")
