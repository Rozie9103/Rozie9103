import requests

def validate_proxy(proxy_url, test_url="https://www.google.com", timeout=10):
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }
    try:
        resp = requests.get(test_url, proxies=proxies, timeout=timeout)
        return resp.status_code == 200
    except Exception as e:
        return False

def validate_proxies_from_file(proxy_file):
    valid = []
    with open(proxy_file) as f:
        for line in f:
            proxy = line.strip()
            if proxy and validate_proxy(proxy):
                print(f"[OK] {proxy}")
                valid.append(proxy)
            else:
                print(f"[FAIL] {proxy}")
    return valid

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python proxy_validation.py proxylist.txt")
        exit(1)
    valid = validate_proxies_from_file(sys.argv[1])
    print(f"Valid proxies: {len(valid)}")