import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from utils_config import console
import time

class URLHandler:
    def __init__(self, use_tor=False, proxy=None, user_agent=None):
        self.session = self._setup_session(use_tor, proxy, user_agent)
        self.cookies = {}
    
    def _setup_session(self, use_tor=False, proxy=None, user_agent=None):
        session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504, 403],
            allowed_methods=["HEAD", "GET", "POST"],
            respect_retry_after_header=True
        )
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=100)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        # Configure proxies if specified
        if proxy:
            session.proxies = {"http": proxy, "https": proxy}
        elif use_tor:
            session.proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
        
        # Set custom user agent if provided
        if user_agent:
            session.headers.update({"User-Agent": user_agent})
        else:
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            
        return session

    def validate_url(self, url):
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
                
            # Facebook login.php is always valid
            if "facebook.com" in url and ("login.php" in url or "/login" in url):
                return True
                
            # Only allow http/https
            if parsed.scheme not in ["http", "https"]:
                return False
                
            try:
                head_response = self.session.head(url, timeout=10, allow_redirects=True)
                if head_response.status_code in [200, 301, 302, 403]:
                    # Store cookies from the response
                    self.cookies.update(dict(head_response.cookies))
                    return True
                
                response = self.session.get(url, timeout=10)
                # Store cookies from the response
                self.cookies.update(dict(response.cookies))
                return response.status_code == 200
            except requests.Timeout:
                console.print(f"[yellow]URL Validation Timeout: {url}[/yellow]")
                return False
            except requests.ConnectionError:
                console.print(f"[yellow]URL Connection Error: {url}[/yellow]")
                return False
                
            return True
        except Exception as e:
            console.print(f"[red]URL Validation Error: {e}[/red]")
            return False

    def extract_form_fields(self, url):
        """
        Extract form fields from a given URL, focusing on login forms.
        Returns a dictionary with field mappings.
        """
        # Special handling for Facebook login - always return this mapping for Facebook
        if "facebook.com" in url and ("login.php" in url or "/login" in url):
            return {
                "target_url": url,
                "username_field": "email",
                "password_field": "pass",
                "submit": "login"
            }
            
        try:
            response = self.session.get(url, timeout=10)
            # Store cookies from the response
            self.cookies.update(dict(response.cookies))
            soup = BeautifulSoup(response.text, 'html.parser')
            form = soup.find('form')
            if not form:
                return {}
            
            fields = {}
            inputs = form.find_all('input')
            for input in inputs:
                name = input.get('name')
                value = input.get('value', '')
                if name:
                    if input.get('type') == 'password':
                        fields['password_field'] = name
                    elif input.get('type') in ['text', 'email']:
                        fields['username_field'] = name
                    elif input.get('type') == 'hidden':
                        fields[name] = value
                    elif input.get('type') == 'submit':
                        fields['submit'] = name
                    # Detect CSRF token
                    if 'csrf' in name.lower() or 'token' in name.lower():
                        fields['csrf_token'] = {'name': name, 'value': value}
            
            action = form.get('action', '')
            
            # Properly handle the form action URL
            if action:
                fields['target_url'] = urljoin(url, action)
            else:
                fields['target_url'] = url
                
            return fields
        except requests.Timeout:
            console.print(f"[yellow]Form Extraction Timeout: {url}[/yellow]")
            return {}
        except requests.ConnectionError:
            console.print(f"[yellow]Form Extraction Connection Error: {url}[/yellow]")
            return {}
        except Exception as e:
            console.print(f"[red]Form Extraction Error: {e}[/red]")
            return {}
            
    def detect_login_endpoint(self, base_url):
        """
        Crawl the main page and automatically find login forms.
        Returns the login endpoint URL and field mapping.
        """
        try:
            # Handle Facebook specially - always return the login URL and fields
            if "facebook.com" in base_url:
                login_url = "https://www.facebook.com/login.php"
                fields = {
                    "target_url": login_url,
                    "username_field": "email",
                    "password_field": "pass",
                    "submit": "login"
                }
                return login_url, fields
            
            try:
                response = self.session.get(base_url, timeout=10)
                # Store cookies from the response
                self.cookies.update(dict(response.cookies))
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Common login paths to check if no form is found on the main page
                common_paths = [
                    '/login', '/signin', '/auth', '/account/login',
                    '/user/login', '/members/login', '/membership/login',
                    '/login.php', '/user/signin', '/log-in'
                ]
                
                # First, look for login links
                login_links = []
                for a in soup.find_all('a', href=True):
                    href = a.get('href')
                    text = a.text.lower()
                    if 'login' in text or 'sign in' in text or 'log in' in text:
                        login_links.append(href)
                
                # Check login links first
                for link in login_links:
                    full_url = urljoin(base_url, link)
                    login_form = self._check_for_login_form(full_url)
                    if login_form:
                        return full_url, login_form
                
                # Check for forms on the main page
                main_page_form = self._check_for_login_form(base_url)
                if main_page_form:
                    return base_url, main_page_form
                    
                # Try common login paths
                for path in common_paths:
                    potential_url = urljoin(base_url, path)
                    login_form = self._check_for_login_form(potential_url)
                    if login_form:
                        return potential_url, login_form
            except requests.Timeout:
                console.print(f"[yellow]Login Endpoint Detection Timeout: {base_url}[/yellow]")
            except requests.ConnectionError:
                console.print(f"[yellow]Login Endpoint Connection Error: {base_url}[/yellow]")
                
            return None, None
        except Exception as e:
            console.print(f"[red]Login Endpoint Detection Error: {e}[/red]")
            return None, None
    
    def _check_for_login_form(self, url):
        """
        Helper method to check if a URL contains a login form.
        """
        try:
            try:
                response = self.session.get(url, timeout=10)
                # Store cookies from the response
                self.cookies.update(dict(response.cookies))
                soup = BeautifulSoup(response.text, 'html.parser')
                forms = soup.find_all('form')
                
                for form in forms:
                    # Heuristic: look for forms with password input
                    inputs = form.find_all('input')
                    has_password = any(inp.get('type') == 'password' for inp in inputs)
                    
                    if has_password:
                        fields = {}
                        for input in inputs:
                            name = input.get('name')
                            value = input.get('value', '')
                            if name:
                                if input.get('type') == 'password':
                                    fields['password_field'] = name
                                elif input.get('type') in ['text', 'email']:
                                    fields['username_field'] = name
                                elif input.get('type') == 'hidden':
                                    fields[name] = value
                                elif input.get('type') == 'submit':
                                    fields['submit'] = name
                                # Detect CSRF token
                                if name and ('csrf' in name.lower() or 'token' in name.lower()):
                                    fields['csrf_token'] = {'name': name, 'value': value}
                        
                        action = form.get('action', '')
                        if action:
                            fields['target_url'] = urljoin(url, action)
                        else:
                            fields['target_url'] = url
                            
                        return fields
                return None
            except requests.Timeout:
                console.print(f"[yellow]Form Check Timeout: {url}[/yellow]")
                return None
            except requests.ConnectionError:
                console.print(f"[yellow]Form Check Connection Error: {url}[/yellow]")
                return None
        except Exception as e:
            console.print(f"[red]Form Check Error: {e}[/red]")
            return None
            
    def submit_form(self, url, data, method="POST", additional_headers=None):
        """
        Submit a form with the given data and method.
        Returns the response object.
        """
        try:
            headers = {}
            if additional_headers:
                headers.update(additional_headers)
                
            # Add cookies to the request
            if self.cookies:
                self.session.cookies.update(self.cookies)
            
            try:    
                if method.upper() == "POST":
                    response = self.session.post(url, data=data, headers=headers, timeout=15)
                else:
                    response = self.session.get(url, params=data, headers=headers, timeout=15)
                    
                # Update cookies from the response
                self.cookies.update(dict(response.cookies))
                return response
            except requests.Timeout:
                console.print(f"[yellow]Form Submission Timeout: {url}[/yellow]")
                return None
            except requests.ConnectionError:
                console.print(f"[yellow]Form Submission Connection Error: {url}[/yellow]")
                return None
        except Exception as e:
            console.print(f"[red]Form Submission Error: {e}[/red]")
            return None

    def validate_url(self, url):
        # Tambahkan pengecekan agar domain facebook.com dan endpoint login.php dianggap valid
        if "facebook.com" in url and ("/login" in url or "login.php" in url):
            return True
        try:
            head_response = self.session.head(url, timeout=10, allow_redirects=True)
            if head_response.status_code in [200, 301, 302, 403]:
                # Store cookies from the response
                self.cookies.update(dict(head_response.cookies))
                return True
            
            response = self.session.get(url, timeout=10)
            # Store cookies from the response
            self.cookies.update(dict(response.cookies))
            return response.status_code == 200
        except Exception as e:
            console.print(f"[red]URL Validation Error: {e}[/red]")
            return False

    # This is a duplicate method that's been removed
        except Exception as e:
            console.print(f"[red]Form Extraction Error: {e}[/red]")
            return {}
            
    def detect_login_endpoint(self, base_url):
        """
        Crawl the main page and automatically find login forms.
        Returns the login endpoint URL and field mapping.
        """
        try:
            response = self.session.get(base_url, timeout=10)
            # Store cookies from the response
            self.cookies.update(dict(response.cookies))
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Common login paths to check if no form is found on the main page
            common_paths = [
                '/login', '/signin', '/auth', '/account/login',
                '/user/login', '/members/login', '/membership/login'
            ]
            
            # First, look for login links
            login_links = []
            for a in soup.find_all('a', href=True):
                href = a.get('href')
                text = a.text.lower()
                if 'login' in text or 'sign in' in text or 'log in' in text:
                    login_links.append(href)
            
            # Check login links first
            for link in login_links:
                full_url = urljoin(base_url, link)
                login_form = self._check_for_login_form(full_url)
                if login_form:
                    return full_url, login_form
            
            # Check for forms on the main page
            main_page_form = self._check_for_login_form(base_url)
            if main_page_form:
                return base_url, main_page_form
                
            # Try common login paths
            for path in common_paths:
                potential_url = urljoin(base_url, path)
                login_form = self._check_for_login_form(potential_url)
                if login_form:
                    return potential_url, login_form
                    
            return None, None
        except Exception as e:
            console.print(f"[red]Login Endpoint Detection Error: {e}[/red]")
            return None, None
    
    def _check_for_login_form(self, url):
        """
        Helper method to check if a URL contains a login form.
        """
        try:
            response = self.session.get(url, timeout=10)
            # Store cookies from the response
            self.cookies.update(dict(response.cookies))
            soup = BeautifulSoup(response.text, 'html.parser')
            forms = soup.find_all('form')
            
            for form in forms:
                # Heuristic: look for forms with password input
                inputs = form.find_all('input')
                has_password = any(inp.get('type') == 'password' for inp in inputs)
                
                if has_password:
                    fields = {}
                    for input in inputs:
                        name = input.get('name')
                        value = input.get('value', '')
                        if name:
                            if input.get('type') == 'password':
                                fields['password_field'] = name
                            elif input.get('type') in ['text', 'email']:
                                fields['username_field'] = name
                            elif input.get('type') == 'hidden':
                                fields[name] = value
                            # Detect CSRF token
                            if name and ('csrf' in name.lower() or 'token' in name.lower()):
                                fields['csrf_token'] = {'name': name, 'value': value}
                    
                    action = form.get('action', '')
                    if action:
                        fields['target_url'] = urljoin(url, action)
                    else:
                        fields['target_url'] = url
                        
                    return fields
            return None
        except Exception as e:
            console.print(f"[red]Form Check Error: {e}[/red]")
            return None
            
    def submit_form(self, url, data, method="POST", additional_headers=None):
        """
        Submit a form with the given data and method.
        Returns the response object.
        """
        try:
            headers = {}
            if additional_headers:
                headers.update(additional_headers)
                
            # Add cookies to the request
            if self.cookies:
                self.session.cookies.update(self.cookies)
                
            if method.upper() == "POST":
                response = self.session.post(url, data=data, headers=headers, timeout=15)
            else:
                response = self.session.get(url, params=data, headers=headers, timeout=15)
                
            # Update cookies from the response
            self.cookies.update(dict(response.cookies))
            return response
        except Exception as e:
            console.print(f"[red]Form Submission Error: {e}[/red]")
            return None
