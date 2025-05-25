import random
import time
import logging

class ProxyHandler:
    def __init__(self, proxy_file=None, max_failures=3):
        """
        Initialize the advanced proxy handler with rotation and blacklisting
        
        Args:
            proxy_file: path to file containing proxy list (optional)
            max_failures: maximum number of failures before permanent blacklist
        """
        self.proxy_list = []
        self.failed_proxies = set()
        self.failure_count = {}  # Track number of failures per proxy
        self.max_failures = max_failures
        self.index = 0
        self.last_used = {}  # Track when proxy was last used
        
        # Configure logging
        self.logger = logging.getLogger('ProxyHandler')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        if proxy_file:
            self.load_from_file(proxy_file)

    def load_from_file(self, proxy_file):
        """
        Load proxies from file (one proxy per line, format: ip:port or protocol://ip:port)
        """
        try:
            with open(proxy_file, "r") as f:
                self.proxy_list = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            self.logger.info(f"Successfully loaded {len(self.proxy_list)} proxies from {proxy_file}")
            self.index = 0
        except Exception as e:
            self.logger.error(f"Failed to load proxies from file: {e}")

    def get_next_proxy(self, rotation_mode="round-robin", cooldown_seconds=0):
        """
        Get next proxy using specified rotation strategy
        
        Args:
            rotation_mode: Strategy for proxy rotation ("round-robin", "random", or "least-used")
            cooldown_seconds: Minimum seconds between reusing the same proxy
            
        Returns:
            str: Proxy URL or None if no proxies available
        """
        available = [p for p in self.proxy_list if p not in self.failed_proxies]
        if not available:
            self.logger.warning("No available proxies remaining")
            return None
            
        # Apply cooldown filter if specified
        if cooldown_seconds > 0:
            current_time = time.time()
            available = [p for p in available if current_time - self.last_used.get(p, 0) >= cooldown_seconds]
            if not available:
                self.logger.debug("All proxies are in cooldown period, using first available")
                # If all are in cooldown, just use the one with the oldest use time
                return min(self.proxy_list, key=lambda p: self.last_used.get(p, 0))
        
        # Select proxy based on rotation strategy
        if rotation_mode == "random":
            proxy = random.choice(available)
        elif rotation_mode == "least-used":
            proxy = min(available, key=lambda p: self.failure_count.get(p, 0))
        else:  # Default: round-robin
            proxy = available[self.index % len(available)]
            self.index += 1
            
        # Record usage time
        self.last_used[proxy] = time.time()
        return proxy

    def mark_proxy_failed(self, proxy_url):
        """
        Mark a proxy as failed (temporary blacklist)
        
        Args:
            proxy_url: The proxy URL that failed
            
        Returns:
            bool: True if proxy was permanently blacklisted, False otherwise
        """
        if proxy_url not in self.proxy_list:
            return False
            
        # Increment failure count
        self.failure_count[proxy_url] = self.failure_count.get(proxy_url, 0) + 1
        
        # Add to failed set
        self.failed_proxies.add(proxy_url)
        
        # Log the failure
        self.logger.debug(f"Proxy {proxy_url} marked as failed (count: {self.failure_count[proxy_url]})")
        
        # Check if max failures reached
        if self.failure_count[proxy_url] >= self.max_failures:
            self.logger.warning(f"Proxy {proxy_url} permanently blacklisted after {self.max_failures} failures")
            return True
        return False

    def reset_failed(self, reset_counts=False):
        """
        Reset the failed proxies blacklist
        
        Args:
            reset_counts: If True, also reset the failure counters
        """
        self.failed_proxies.clear()
        if reset_counts:
            self.failure_count.clear()
        self.logger.info("Reset failed proxies blacklist" + (" and failure counts" if reset_counts else ""))

    def validate_proxy(self, proxy_url, test_url="http://example.com", timeout=5):
        """
        Validate proxy by making a simple request (requires requests library)
        
        Args:
            proxy_url: Proxy URL to validate
            test_url: URL to test against
            timeout: Request timeout in seconds
            
        Returns:
            bool: True if proxy works, False otherwise
        """
        try:
            import requests
            # Format proxy correctly based on whether it has protocol prefix
            if '://' in proxy_url:
                protocol = proxy_url.split('://')[0]
                proxies = {protocol: proxy_url}
            else:
                proxies = {"http": f"http://{proxy_url}", "https": f"http://{proxy_url}"}
                
            self.logger.debug(f"Testing proxy {proxy_url} against {test_url}")
            resp = requests.get(test_url, proxies=proxies, timeout=timeout)
            success = resp.status_code == 200
            
            if success:
                self.logger.debug(f"Proxy {proxy_url} validation successful")
            else:
                self.logger.debug(f"Proxy {proxy_url} returned status code {resp.status_code}")
                
            return success
        except Exception as e:
            self.logger.debug(f"Proxy {proxy_url} validation failed: {str(e)}")
            return False

    def shuffle(self):
        """
        Shuffle the proxy list (for randomization)
        """
        random.shuffle(self.proxy_list)
        self.logger.debug("Proxy list shuffled")
        
    def add_proxy(self, proxy_url):
        """
        Add a single proxy to the list
        
        Args:
            proxy_url: Proxy URL to add
            
        Returns:
            bool: True if proxy was added, False if it already existed
        """
        if proxy_url not in self.proxy_list:
            self.proxy_list.append(proxy_url)
            self.logger.debug(f"Added proxy {proxy_url}")
            return True
        return False
            
    def get_working_proxies(self):
        """
        Get list of currently working (non-failed) proxies
        
        Returns:
            list: List of working proxy URLs
        """
        return [p for p in self.proxy_list if p not in self.failed_proxies]
        
    def save_to_file(self, filename):
        """
        Save current proxy list to file
        
        Args:
            filename: Path to save the proxy list
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(filename, 'w') as f:
                for proxy in self.proxy_list:
                    f.write(f"{proxy}\n")
            self.logger.info(f"Saved {len(self.proxy_list)} proxies to {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save proxies to file: {e}")
            return False
            
    def validate_all(self, test_url="http://example.com", timeout=5, parallel=False):
        """
        Validate all proxies and filter out non-working ones
        
        Args:
            test_url: URL to test against
            timeout: Request timeout in seconds
            parallel: If True, validate in parallel using ThreadPoolExecutor
            
        Returns:
            tuple: (working_count, failed_count)
        """
        working = 0
        failed = 0
        
        if parallel:
            try:
                from concurrent.futures import ThreadPoolExecutor
                self.logger.info(f"Validating {len(self.proxy_list)} proxies in parallel...")
                
                def validate_and_count(proxy):
                    if self.validate_proxy(proxy, test_url, timeout):
                        return True
                    else:
                        self.mark_proxy_failed(proxy)
                        return False
                
                with ThreadPoolExecutor(max_workers=min(20, len(self.proxy_list))) as executor:
                    results = list(executor.map(validate_and_count, self.proxy_list))
                    working = sum(results)
                    failed = len(results) - working
            except ImportError:
                self.logger.warning("ThreadPoolExecutor not available, falling back to sequential validation")
                parallel = False
                
        if not parallel:
            self.logger.info(f"Validating {len(self.proxy_list)} proxies sequentially...")
            for proxy in self.proxy_list:
                if self.validate_proxy(proxy, test_url, timeout):
                    working += 1
                else:
                    self.mark_proxy_failed(proxy)
                    failed += 1
                    
        self.logger.info(f"Proxy validation complete: {working} working, {failed} failed")
        return working, failed
