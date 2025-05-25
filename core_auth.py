import os
import re
import bcrypt
import getpass
import secrets
import datetime
import time
from cryptography.fernet import Fernet
from utils_config import console

class SecuritySystem:
    def __init__(self):
        self.auth_token = self._load_or_create_auth()
        self.encryption_key = self._load_or_create_encryption_key()
        self.audit_log_file = os.path.join(os.getcwd(), "audit.log")
        self.valid_users = self._load_users()
        self.lockout_threshold = 5
        self.lockout_time = 300  # seconds (5 minutes)
        self.failed_attempts = {}
    
    def _load_users(self):
        """Load user credentials from secure storage"""
        users_file = os.path.join(os.getcwd(), "users.sec")
        if os.path.exists(users_file):
            users = {}
            with open(users_file, "r") as f:
                for line in f:
                    if ":" in line:
                        username, hashed = line.strip().split(":", 1)
                        users[username] = hashed
            return users
        else:
            # Create default admin user if no users file exists
            admin_password = self._create_secure_password("admin")
            users = {"admin": admin_password}
            self._save_users(users)
            return users
    
    def _save_users(self, users):
        """Save user credentials to secure storage"""
        users_file = os.path.join(os.getcwd(), "users.sec")
        with open(users_file, "w") as f:
            for username, hashed in users.items():
                f.write(f"{username}:{hashed}\n")
        os.chmod(users_file, 0o600)  # Restrict file permissions
    
    def _load_or_create_auth(self):
        auth_file = os.path.join(os.getcwd(), "auth.sec")
        if os.path.exists(auth_file):
            with open(auth_file, "rb") as f:
                hashed = f.read()
            return hashed
        
        console.print("[bold cyan]=== ROZIE Initial Setup ===[/bold cyan]")
        password = self._create_secure_password("master")
        
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        with open(auth_file, "wb") as f:
            f.write(hashed)
        os.chmod(auth_file, 0o600)  # Restrict file permissions
        return hashed
    
    def _create_secure_password(self, user_type):
        """Create a secure password with validation"""
        while True:
            password = getpass.getpass(f"Set {user_type} password for ROZIE: ")
            
            # Password strength validation
            if len(password) < 8:
                console.print("[red]Password must be at least 8 characters long![/red]")
                continue
                
            if not re.search(r"[A-Z]", password):
                console.print("[red]Password must contain at least one uppercase letter![/red]")
                continue
                
            if not re.search(r"[a-z]", password):
                console.print("[red]Password must contain at least one lowercase letter![/red]")
                continue
                
            if not re.search(r"[0-9]", password):
                console.print("[red]Password must contain at least one number![/red]")
                continue
                
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
                console.print("[red]Password must contain at least one special character![/red]")
                continue
            
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                console.print("[red]Passwords do not match![/red]")
                continue
            
            return password
    
    def authenticate(self):
        console.print("[bold cyan]=== ROZIE Authentication System ===[/bold cyan]")
        
        # Check for account lockouts
        self._clean_lockouts()
        
        username = input("Username: ").strip()
        
        # Check if user is locked out
        if username in self.failed_attempts and self.failed_attempts[username]["count"] >= self.lockout_threshold:
            lockout_time = self.failed_attempts[username]["time"] + self.lockout_time
            if time.time() < lockout_time:
                remaining = int(lockout_time - time.time())
                self._audit_log(f"Attempted login to locked account: {username}")
                console.print(f"[red]Account locked. Try again in {remaining} seconds.[/red]")
                return False
        
        # Check if user exists
        if username not in self.valid_users:
            self._audit_log(f"Login attempt with invalid username: {username}")
            console.print("[red]Authentication failed![/red]")
            return False
        
        # Password authentication
        attempts = 3
        while attempts > 0:
            password = getpass.getpass(f"Password (Attempts left: {attempts}): ")
            
            if bcrypt.checkpw(password.encode(), self.auth_token):
                if self._two_factor_auth():
                    # Reset failed attempts on successful login
                    if username in self.failed_attempts:
                        del self.failed_attempts[username]
                    
                    self._audit_log(f"Authentication success for user: {username}")
                    console.print("[green]Authentication successful![/green]")
                    return True
                else:
                    self._audit_log(f"2FA failed for user: {username}")
                    console.print("[red]2FA failed![/red]")
                    return False
            
            # Track failed attempts
            if username not in self.failed_attempts:
                self.failed_attempts[username] = {"count": 0, "time": time.time()}
            
            self.failed_attempts[username]["count"] += 1
            self.failed_attempts[username]["time"] = time.time()
            
            attempts -= 1
            self._audit_log(f"Wrong password attempt for user: {username}")
            console.print(f"[red]Wrong password! Attempts left: {attempts}[/red]")
            
            # Check for lockout threshold
            if self.failed_attempts[username]["count"] >= self.lockout_threshold:
                self._audit_log(f"Account locked due to too many failed attempts: {username}")
                console.print(f"[red]Too many failed attempts! Account locked for {self.lockout_time/60} minutes.[/red]")
                return False
                
        self._audit_log(f"Too many failed attempts for user: {username}")
        console.print("[red]Too many failed attempts![/red]")
        return False
    
    def _clean_lockouts(self):
        """Clean expired lockouts"""
        current_time = time.time()
        expired = []
        
        for username, data in self.failed_attempts.items():
            if current_time > data["time"] + self.lockout_time:
                expired.append(username)
                
        for username in expired:
            del self.failed_attempts[username]
        
    def _two_factor_auth(self):
        code = str(secrets.randbelow(1000000)).zfill(6)
        console.print(f"[bold blue][2FA] Your verification code: {code}[/bold blue]")
        
        # Add timeout for 2FA
        start_time = time.time()
        timeout = 60  # seconds
        
        console.print(f"[yellow]Code valid for {timeout} seconds[/yellow]")
        user_code = getpass.getpass("Enter 2FA code: ")
        
        # Check if code has expired
        if time.time() - start_time > timeout:
            self._audit_log("2FA code expired")
            console.print("[red]Verification code expired![/red]")
            return False
            
        return user_code == code

    def _load_or_create_encryption_key(self):
        key_file = os.path.join(os.getcwd(), "rozie.key")
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                key = f.read()
            # Verify key is valid Fernet key
            try:
                Fernet(key)
                return key
            except Exception:
                console.print("[yellow]Existing encryption key is invalid. Generating new key...[/yellow]")
        
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        os.chmod(key_file, 0o600)  # Restrict file permissions
        self._audit_log("New encryption key generated")
        return key

    def secure_wipe(self, data):
        if isinstance(data, bytearray):
            for i in range(len(data)):
                data[i] = 0
                
    def _audit_log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.audit_log_file, "a") as log:
                log.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            console.print(f"[red]Failed to write to audit log: {str(e)}[/red]")
            
    def rotate_encryption_key(self):
        """Generates a new encryption key and backs up the old one"""
        old_key_file = os.path.join(os.getcwd(), f"rozie.key.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
        with open(old_key_file, "wb") as f:
            f.write(self.encryption_key)
        os.chmod(old_key_file, 0o600)  # Restrict file permissions
            
        self.encryption_key = Fernet.generate_key()
        with open(os.path.join(os.getcwd(), "rozie.key"), "wb") as f:
            f.write(self.encryption_key)
        os.chmod(os.path.join(os.getcwd(), "rozie.key"), 0o600)  # Restrict file permissions
            
        self._audit_log("Encryption key rotated")
        return self.encryption_key
        
    def add_user(self, admin_password):
        """Add a new user to the system"""
        # Verify admin password first
        if not bcrypt.checkpw(admin_password.encode(), self.auth_token):
            self._audit_log("Failed attempt to add user - invalid admin password")
            console.print("[red]Invalid admin password![/red]")
            return False
            
        username = input("Enter new username: ").strip()
        
        # Validate username
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            console.print("[red]Username must be 3-20 characters and contain only letters, numbers, and underscores[/red]")
            return False
            
        if username in self.valid_users:
            console.print("[red]Username already exists![/red]")
            return False
            
        password = self._create_secure_password("user")
        
        # Hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt).decode()
        
        # Add to users dictionary
        self.valid_users[username] = hashed
        self._save_users(self.valid_users)
        
        self._audit_log(f"New user added: {username}")
        console.print(f"[green]User {username} added successfully![/green]")
        return True
        
    def remove_user(self, admin_password, username):
        """Remove a user from the system"""
        # Verify admin password first
        if not bcrypt.checkpw(admin_password.encode(), self.auth_token):
            self._audit_log("Failed attempt to remove user - invalid admin password")
            console.print("[red]Invalid admin password![/red]")
            return False
            
        if username not in self.valid_users:
            console.print("[red]Username does not exist![/red]")
            return False
            
        # Don't allow removing the last user
        if len(self.valid_users) <= 1:
            console.print("[red]Cannot remove the last user![/red]")
            return False
            
        del self.valid_users[username]
        self._save_users(self.valid_users)
        
        self._audit_log(f"User removed: {username}")
        console.print(f"[green]User {username} removed successfully![/green]")
        return True
