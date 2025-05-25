import logging
import sys
import os
from utils_config import console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src directory to path so we can import our enhanced module
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import our enhanced login detector
from core.login_detector import LoginEndpointDetector as EnhancedLoginDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='login_detector.log'
)
logger = logging.getLogger('login_detector')

class LoginEndpointDetector:
    """
    Enhanced automatic login endpoint and form field detection module.
    Uses advanced detection techniques to identify login forms on target websites.
    
    Features:
    - Login endpoint detection
    - Username and password field identification
    - Token extraction
    - URL validation
    - Crawling capabilities
    """

    def __init__(self, use_tor=False, proxy=None, stealth=True, max_depth=3, timeout=10):
        """
        Initialize the login endpoint detector
        
        Args:
            use_tor (bool): Whether to route through TOR
            proxy (str): Proxy URL to use
            stealth (bool): Whether to use stealth mode
            max_depth (int): Maximum crawl depth
            timeout (int): Request timeout in seconds
        """
        # Create instance of enhanced detector
        self.detector = EnhancedLoginDetector(
            use_tor=use_tor,
            proxy=proxy,
            stealth=stealth,
            max_depth=max_depth,
            timeout=timeout
        )
        
        # Store parameters for stats
        self.stealth = stealth
        self.max_depth = max_depth
        self.timeout = timeout
        self.success_rate = 0
        
        logger.info(f"LoginEndpointDetector initialized: stealth={stealth}, tor={use_tor}, proxy={proxy}")

    def find_login_endpoint(self, base_url):
        """
        Detect login endpoint and form fields on a website.
        
        Args:
            base_url: Main URL of the target website
            
        Returns:
            tuple: (login_url, field_info) or (None, None) if detection fails
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task("[cyan]Analyzing target website...", total=None)
            
            # Use enhanced detector to find login endpoint
            result = self.detector.find_login_endpoint(base_url)
            
            # Update success rate if found
            if result and result[0]:
                self.success_rate += 0.1  # Increment success rate
                
            return result
        
    def get_stats(self):
        """Return statistics about detector usage"""
        detector_stats = self.detector.get_stats()
        return {
            "success_rate": self.success_rate,
            "stealth_mode": self.stealth,
            "max_depth": self.max_depth,
            "visited_urls": detector_stats.get("visited_urls", 0)
        }
