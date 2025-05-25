import sys
import traceback
import re
import argparse
import os
import importlib
import platform
import socket
import requests
import random
import threading
import time
from datetime import datetime

# Core modules
from core_auth import SecuritySystem
from interfaces_cli import display_attack_result, export_results
from core_attack_engine import BruteForceEngine
from core_detection_module import LoginEndpointDetector
from utils_config import console, load_config
from utils_logger import get_logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.align import Align
from rich.prompt import Prompt
from rich.theme import Theme
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

try:
    from pyfiglet import Figlet
except ImportError:
    Figlet = None

console_rich = Console(theme=Theme({
    "menu": "bold cyan",
    "option": "bold magenta",
    "input": "bold yellow",
    "success": "bold green",
    "error": "bold red",
    "info": "bold blue",
    "banner": "bold white on blue",
    "welcome": "bold white on magenta"
}))

# --- ANIMASI & EFEK ---

def typewriter(text, delay=0.03, style=None):
    for char in text:
        if style:
            console_rich.print(char, end='', style=style, soft_wrap=True)
        else:
            console_rich.print(char, end='', soft_wrap=True)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def rainbow_text(text):
    colors = ["red", "yellow", "green", "cyan", "blue", "magenta"]
    t = Text()
    for i, char in enumerate(text):
        t.append(char, style=colors[i % len(colors)])
    console_rich.print(t)

def spinner_effect(text="Brute Forcing..."):
    spinner = SpinnerColumn()
    # Line 68-70
    with Progress(
        SpinnerColumn(),
        *Progress.get_default_columns(),  # Ganti ... dengan kolom default
        transient=True,
        auto_refresh=False
    ) as progress:
        task = progress.add_task(text, total=100)
        for i in range(100):
            time.sleep(0.02)
            progress.update(task, advance=1)
    # Tambahkan pengecekan status live sebelum membuat progress bar
    if not progress.live._started:  # Tambahkan pengecekan status live
        progress.start()

def glitch_text(text, style="bold red"):
    glitched = ""
    for c in text:
        if random.random() < 0.2:
            glitched += random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?")
        else:
            glitched += c
    console_rich.print(glitched, style=style)

def confetti_effect():
    width = 60
    height = 10
    with Live("", refresh_per_second=10, console=console_rich, transient=True) as live:
        for _ in range(20):
            lines = []
            for y in range(height):
                line = ""
                for x in range(width):
                    if random.random() < 0.02:
                        line += f"[bold {random.choice(['red','yellow','green','blue','magenta','cyan'])}]*[/]"
                    else:
                        line += " "
                lines.append(line)
            live.update("\n".join(lines))
            time.sleep(0.08)
    console_rich.print("[bold green]🎉 SUCCESS! Password found! 🎉[/bold green]")

def matrix_effect(stop_event, width=80, height=20, speed=0.07):
    """
    Matrix animation effect with red and green falling characters for brute force visual feedback.
    """
    charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&"
    columns = [0 for _ in range(width)]
    with Live(refresh_per_second=30, console=console_rich, transient=True) as live:
        while not stop_event.is_set():
            matrix_lines = []
            for y in range(height):
                line = ""
                for x in range(width):
                    if random.random() > 0.975:
                        columns[x] = 0
                    # Only show a character if the column is currently "falling"
                    if columns[x] < y:
                        char = random.choice(charset)
                        color = random.choice(["green", "red"])
                        line += f"[{color}]{char}[/]"
                    else:
                        line += "[black] [/]"
                matrix_lines.append(line)
            live.update(Text("\n".join(matrix_lines)))
            time.sleep(speed)

# --- INFO DEVICE/NETWORK/LOKASI ---

def get_device_info():
    info = {
        "OS": platform.system(),
        "OS Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "Python": platform.python_version(),
        "Hostname": socket.gethostname()
    }
    return info

def get_internet_status():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except Exception:
        return False

def get_location_info():
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "IP": data.get("ip", "-"),
                "City": data.get("city", "-"),
                "Region": data.get("region", "-"),
                "Country": data.get("country", "-"),
                "Org": data.get("org", "-"),
                "Loc": data.get("loc", "-")
            }
    except Exception:
        pass
    return {"IP": "-", "City": "-", "Region": "-", "Country": "-", "Org": "-", "Loc": "-"}

# --- WELCOME & BANNER ---

def show_banner():
    banner_text = "ROZIE TOOLKIT"
    if Figlet:
        f = Figlet(font="slant")
        ascii_banner = f.renderText(banner_text)
        console_rich.print(f"[banner]{ascii_banner}[/banner]")
    else:
        rainbow_text(banner_text)

def show_welcome():
    now = datetime.now().strftime("%A, %d %B %Y %H:%M:%S")
    device = get_device_info()
    internet = get_internet_status()
    location = get_location_info()
    user = os.getenv("USERNAME") or os.getenv("USER") or "User"
    device_type = "Mobile" if "android" in device["OS"].lower() or "iphone" in device["OS"].lower() else "Laptop/PC"

    welcome_text = Text(f"Welcome, {user}!", style="welcome")
    subtitle = f"Rozie Toolkit - Your Advanced Brute Force & Security Automation\n[info]{now}[/info]"
    console_rich.print(Panel(welcome_text, subtitle=subtitle, style="magenta", expand=False, border_style="bold magenta"))

    info_table = Table(title="Device & Network Info", box=box.ROUNDED, style="menu")
    info_table.add_column("Property", style="option", no_wrap=True)
    info_table.add_column("Value", style="input")
    info_table.add_row("Device Type", device_type)
    info_table.add_row("OS", device["OS"])
    info_table.add_row("OS Version", device["OS Version"])
    info_table.add_row("Machine", device["Machine"])
    info_table.add_row("Processor", device["Processor"])
    info_table.add_row("Python", device["Python"])
    info_table.add_row("Hostname", device["Hostname"])
    info_table.add_row("Internet", "[success]Connected[/success]" if internet else "[error]Offline[/error]")
    info_table.add_row("IP", location["IP"])
    info_table.add_row("City", location["City"])
    info_table.add_row("Region", location["Region"])
    info_table.add_row("Country", location["Country"])
    info_table.add_row("Org", location["Org"])
    info_table.add_row("Location", location["Loc"])
    console_rich.print(info_table)

# --- FILE DISCOVERY & EXECUTION ---

def discover_py_files(folder):
    folder_path = os.path.join(os.path.dirname(__file__), folder)
    files = []
    if os.path.isdir(folder_path):
        for fname in os.listdir(folder_path):
            if fname.endswith(".py") and not fname.startswith("__"):
                files.append(fname[:-3])
    return files

def run_py_file(folder, file_name):
    files = discover_py_files(folder)
    if file_name not in files:
        console_rich.print(f"[error]File '{file_name}' not found in folder {folder}/[/error]")
        return
    module_name = f"{folder}.{file_name}"
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, "main"):
            console_rich.print(f"[info]Running {folder}: {file_name}[/info]")
            module.main()
        else:
            console_rich.print(f"[error]{folder.capitalize()} '{file_name}' doesn't have a main() function[/error]")
    except Exception as e:
        console_rich.print(f"[error]Error running {folder} '{file_name}': {e}[/error]")

def load_plugins(plugin_folder="plugins"):
    """Load all plugins from the plugin folder that implement PluginInterface"""
    plugins = []
    logger = get_logger()
    
    try:
        # First try to import the interface
        from interfaces.plugin_interface import PluginInterface
        
        for filename in os.listdir(plugin_folder):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    module_name = f"{plugin_folder}.{filename[:-3]}"
                    module = importlib.import_module(module_name)
                    for attr in dir(module):
                        obj = getattr(module, attr)
                        if isinstance(obj, type) and issubclass(obj, PluginInterface) and obj is not PluginInterface:
                            plugin_instance = obj()
                            plugins.append(plugin_instance)
                            logger.info(f"Loaded plugin: {plugin_instance.name}")
                except Exception as e:
                    logger.error(f"Error loading plugin {filename}: {str(e)}")
    except ImportError:
        logger.error("Could not import PluginInterface. Plugin system not available.")
    
    return plugins

def discover_all_folders():
    base = os.path.dirname(__file__)
    return [f for f in os.listdir(base) if os.path.isdir(os.path.join(base, f)) and not f.startswith(".") and f != "__pycache__"]

def is_valid_url(url):
    pattern = r"^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}.*$"
    return re.match(pattern, url) is not None

def safe_input(prompt, validator=None, error_msg="Invalid input."):
    while True:
        value = Prompt.ask(f"[input]{prompt}[/input]")
        if validator is None or validator(value):
            return value
        console_rich.print(f"[error]{error_msg}[/error]")

# --- BRUTE FORCE DENGAN ANIMASI ---

def run_brute_force_attack(target_url, username, wordlist_path=None, username_field=None, 
                          password_field=None, token_fields=None, success_indicator=None, 
                          delay=0.5, threads=5, proxy_path=None, csv_output=None,
                          verbose=True, progress_bar=True):
    field_info = None
    if "/login" not in target_url.lower():
        console_rich.print("[info]Detecting login endpoint...[/info]")
        detector = LoginEndpointDetector()
        login_url, detected_field_info = detector.find_login_endpoint(target_url)
        if login_url:
            console_rich.print(f"[success]Login endpoint detected: {login_url}[/success]")
            target_url = login_url
            field_info = detected_field_info
        else:
            console_rich.print("[error]Could not detect login endpoint. Using provided URL.[/error]")
            if "facebook.com" in target_url and "login.php" in target_url:
                field_info = {
                    "target_url": target_url,
                    "username_field": "email",
                    "password_field": "pass",
                    "submit": "login"
                }
    if field_info is None:
        field_info = {
            "target_url": target_url
        }
    if username_field:
        field_info["username_field"] = username_field
    if password_field:
        field_info["password_field"] = password_field
    if token_fields:
        field_info["token_fields"] = token_fields
    if success_indicator:
        field_info["success_indicator"] = success_indicator
    field_info["delay"] = delay
    field_info["threads"] = threads
    field_info["proxy_path"] = proxy_path
    field_info["wordlist_path"] = wordlist_path
    field_info["csv_output"] = csv_output
    field_info["verbose"] = verbose
    field_info["progress_bar"] = progress_bar
    bf_engine = BruteForceEngine()
    return bf_engine.brute_force(target_url, username, field_info)

def run_brute_force_attack_with_animations(*args, **kwargs):
    # --- Matrix effect + spinner selama brute force berjalan ---
    stop_event = threading.Event()
    try:
        width, height = os.get_terminal_size()
        width = min(width, 120)
        height = min(height-5, 40)
    except Exception:
        width, height = 80, 20

    matrix_thread = threading.Thread(target=matrix_effect, args=(stop_event, width, height, 0.07))
    matrix_thread.start()
    spinner_thread = threading.Thread(target=spinner_effect, args=("Brute Forcing...",))
    spinner_thread.start()
    try:
        result, stats = run_brute_force_attack(*args, **kwargs)
    finally:
        stop_event.set()
        matrix_thread.join()
        spinner_thread.join()
    return result, stats

# --- MAIN MENU INTERAKTIF ---

def interactive_mode():
    show_banner()
    typewriter("Welcome to Rozie Toolkit!", style="bold magenta")
    show_welcome()
    rainbow_text("Rozie Toolkit Main Menu")
    while True:
        menu_panel = Panel(
            Align.center(
                "[menu]Rozie Toolkit Main Menu[/menu]\n"
                "[option]1.[/option] Brute Force Attack\n"
                "[option]2.[/option] Wordlist Generator (Perkembangan)\n"
                "[option]3.[/option] Advanced Mode\n"
                "[option]4.[/option] Run Script from [bold]scripts/[/bold] folder\n"
                "[option]5.[/option] Run Plugin from [bold]plugins/[/bold] folder\n"
                "[option]6.[/option] Run Module from [bold]modules/[/bold] folder\n"
                "[option]7.[/option] Browse All Project Folders & Execute Python Files\n"
                "[option]8.[/option] List All Scripts, Plugins, Modules, and Other Folders\n"
                "[option]0.[/option] Exit",
                vertical="middle"
            ),
            title="[bold magenta]Rozie Toolkit[/bold magenta]",
            border_style="magenta",
            padding=(1, 4),
            expand=False
        )
        console_rich.print(menu_panel)
        choice = Prompt.ask("[input]Choose menu[/input]", choices=[str(i) for i in range(9)], default="0")
        if choice == "1":
            typewriter("Prepare for Brute Force Attack...", style="bold cyan")
            target_url = safe_input(
                "Target Website URL: ",
                validator=is_valid_url,
                error_msg="Input salah! Masukkan URL login website yang valid, misal: https://www.facebook.com/login.php"
            )
            username = safe_input(
                "Username: ",
                validator=lambda x: len(x.strip()) > 0,
                error_msg="Username cannot be empty."
            )
            wordlist_path = safe_input(
                "Path to password wordlist file: ",
                validator=lambda x: len(x.strip()) > 0,
                error_msg="Wordlist path cannot be empty."
            )
            threads = int(safe_input(
                "Number of threads (default 5): ",
                validator=lambda x: x.isdigit() and int(x) > 0,
                error_msg="Threads must be a positive integer."
            ) or 5)
            proxy_path = safe_input(
                "Path to proxy file (optional, press Enter to skip): ",
                validator=lambda x: True,
                error_msg=""
            ) or None
            token_fields = safe_input(
                "Token field names (comma separated, optional): ",
                validator=lambda x: True,
                error_msg=""
            )
            token_fields = [f.strip() for f in token_fields.split(",") if f.strip()] if token_fields else None
            success_indicator = safe_input(
                "Success indicator (optional, string on successful login page): ",
                validator=lambda x: True,
                error_msg=""
            ) or None
            delay = float(safe_input(
                "Delay between requests in seconds (default 0.5): ",
                validator=lambda x: x.replace('.', '', 1).isdigit(),
                error_msg="Delay must be a number."
            ) or 0.5)
            csv_output = safe_input(
                "Path to CSV output file (optional, press Enter to skip): ",
                validator=lambda x: True,
                error_msg=""
            ) or None
            verbose = safe_input(
                "Verbose mode? (y/n, default y): ",
                validator=lambda x: x.lower() in ("y", "n", ""),
                error_msg="Input must be y or n."
            ).lower() or "y"
            verbose = verbose == "y"
            progress_bar = safe_input(
                "Show progress bar? (y/n, default y): ",
                validator=lambda x: x.lower() in ("y", "n", ""),
                error_msg="Input must be y or n."
            ).lower() or "y"
            progress_bar = progress_bar == "y"
            # === MATRIX & SPINNER EFFECT BRUTE FORCE ===
            result, stats = run_brute_force_attack_with_animations(
                target_url=target_url,
                username=username,
                wordlist_path=wordlist_path,
                threads=threads,
                proxy_path=proxy_path,
                token_fields=token_fields,
                success_indicator=success_indicator,
                delay=delay,
                csv_output=csv_output,
                verbose=verbose,
                progress_bar=progress_bar
            )
            display_attack_result(result, stats)
            if csv_output and result and result.get("success"):
                confetti_effect()
                export_results(result, stats, csv_output)
            elif not (result and result.get("success")):
                glitch_text("❌ No password found!")
        elif choice == "2":
            spinner_effect("Wordlist Generator coming soon...")
            console_rich.print("[info]Wordlist Generator & Customization coming soon.[/info]")
        elif choice == "3":
            spinner_effect("Starting Advanced Mode...")
            console_rich.print("[info]Launching Advanced Mode with dynamic plugin system...[/info]")
            try:
                import advanced_mode
                advanced_mode.main()
            except ImportError as e:
                console_rich.print(f"[error]Error importing advanced_mode: {e}[/error]")
            except Exception as e:
                console_rich.print(f"[error]Error in Advanced Mode: {e}[/error]")
        elif choice == "4":
            scripts = discover_py_files("scripts")
            if not scripts:
                glitch_text("No scripts found in scripts/ folder")
            else:
                table = Table(title="Available Scripts", box=box.SIMPLE)
                table.add_column("No", style="option")
                table.add_column("Script", style="input")
                for idx, s in enumerate(scripts, 1):
                    table.add_row(str(idx), s)
                console_rich.print(table)
                idx = safe_input("Choose script number to run: ", validator=lambda x: x.isdigit() and 1 <= int(x) <= len(scripts), error_msg="Invalid choice.")
                run_py_file("scripts", scripts[int(idx)-1])
        elif choice == "5":
            plugins = discover_py_files("plugins")
            if not plugins:
                glitch_text("No plugins found in plugins/ folder")
            else:
                table = Table(title="Available Plugins", box=box.SIMPLE)
                table.add_column("No", style="option")
                table.add_column("Plugin", style="input")
                for idx, p in enumerate(plugins, 1):
                    table.add_row(str(idx), p)
                console_rich.print(table)
                idx = safe_input("Choose plugin number to run: ", validator=lambda x: x.isdigit() and 1 <= int(x) <= len(plugins), error_msg="Invalid choice.")
                run_py_file("plugins", plugins[int(idx)-1])
        elif choice == "6":
            modules = discover_py_files("modules")
            if not modules:
                glitch_text("No modules found in modules/ folder")
            else:
                table = Table(title="Available Modules", box=box.SIMPLE)
                table.add_column("No", style="option")
                table.add_column("Module", style="input")
                for idx, m in enumerate(modules, 1):
                    table.add_row(str(idx), m)
                console_rich.print(table)
                idx = safe_input("Choose module number to run: ", validator=lambda x: x.isdigit() and 1 <= int(x) <= len(modules), error_msg="Invalid choice.")
                run_py_file("modules", modules[int(idx)-1])
        elif choice == "7":
            folders = discover_all_folders()
            if not folders:
                glitch_text("No folders found.")
            else:
                table = Table(title="Available Folders", box=box.SIMPLE)
                table.add_column("No", style="option")
                table.add_column("Folder", style="input")
                for idx, folder in enumerate(folders, 1):
                    table.add_row(str(idx), folder)
                console_rich.print(table)
                folder_idx = safe_input("Choose folder number to browse: ", validator=lambda x: x.isdigit() and 1 <= int(x) <= len(folders), error_msg="Invalid choice.")
                folder = folders[int(folder_idx)-1]
                files = discover_py_files(folder)
                if not files:
                    glitch_text(f"No Python files in {folder}/ folder")
                else:
                    table2 = Table(title=f"Python files in {folder}/", box=box.SIMPLE)
                    table2.add_column("No", style="option")
                    table2.add_column("File", style="input")
                    for idx, f in enumerate(files, 1):
                        table2.add_row(str(idx), f)
                    console_rich.print(table2)
                    file_idx = safe_input("Choose file number to run: ", validator=lambda x: x.isdigit() and 1 <= int(x) <= len(files), error_msg="Invalid choice.")
                    run_py_file(folder, files[int(file_idx)-1])
        elif choice == "8":
            print("=== Scripts ===")
            for s in discover_py_files("scripts"):
                print(f"  {s}")
            print("=== Plugins ===")
            for p in discover_py_files("plugins"):
                print(f"  {p}")
            print("=== Modules ===")
            for m in discover_py_files("modules"):
                print(f"  {m}")
            other_folders = [f for f in discover_all_folders() if f not in ["scripts", "plugins", "modules", "__pycache__"]]
            if other_folders:
                print("=== Other Folders ===")
                for folder in other_folders:
                    print(f"  {folder}/")
                    files = discover_py_files(folder)
                    for f in files:
                        print(f"    - {f}")
        elif choice == "0":
            typewriter("Thank you for using Rozie Toolkit! Goodbye!", style="bold green")
            break
        else:
            glitch_text("Invalid choice. Try again.")

# --- ARGUMENT PARSER ---

def parse_arguments():
    parser = argparse.ArgumentParser(description="Brute Force Audit Tool (Multi-thread, Proxy, CSV, Token Scraping, Usability Features)")
    parser.add_argument("--login-url", help="URL endpoint login target")
    parser.add_argument("--username", help="Username target")
    parser.add_argument("--wordlist", help="Path to password wordlist file")
    parser.add_argument("--username-field", help="Username field name (default: auto-detect)")
    parser.add_argument("--password-field", help="Password field name (default: auto-detect)")
    parser.add_argument("--token-fields", nargs="*", help="Dynamic token field names (e.g., csrf_token)")
    parser.add_argument("--success-indicator", help="Unique string on successful login page")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (seconds)")
    parser.add_argument("--threads", type=int, default=5, help="Number of threads (default: 5)")
    parser.add_argument("--proxy-path", help="Path to proxy file (one proxy per line, format http://ip:port)")
    parser.add_argument("--csv-output", help="Path to CSV output file")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--advanced", action="store_true", help="Run in advanced mode with plugin system")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--silent", action="store_true", help="Silent mode (no per-attempt output)")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO", help="Set logging level")
    return parser.parse_args()

# --- MAIN ---

def run_advanced_mode(args):
    """Run the toolkit in advanced mode with plugin system"""
    logger = get_logger(args.log_level)
    config = load_config(args.config) if args.config else {}
    
    logger.info("Rozie Toolkit started in advanced modular mode")
    
    # Load all plugins
    plugins = load_plugins()
    logger.info(f"Loaded {len(plugins)} plugins")
    
    # Run each plugin
    for plugin in plugins:
        try:
            logger.info(f"Running plugin: {plugin.name}")
            plugin.run()
        except Exception as e:
            logger.error(f"Error running plugin {plugin.name}: {str(e)}")
            if args.verbose:
                traceback.print_exc()

def main():
    try:
        args = parse_arguments()
        
        # Setup logger
        logger = get_logger(args.log_level)
        
        # Authentication
        sec_system = SecuritySystem()
        if not sec_system.authenticate():
            glitch_text("Authentication failed. Exiting...")
            logger.error("Authentication failed")
            sys.exit(1)
        
        # Check for advanced mode first
        if args.advanced:
            try:
                run_advanced_mode(args)
                return
            except Exception as e:
                glitch_text(f"Error in advanced mode: {e}")
                logger.error(f"Error in advanced mode: {e}")
                if args.verbose:
                    traceback.print_exc()
                sys.exit(1)
                
        if args.interactive or (not args.login_url and not args.username):
            interactive_mode()
            return
            
        if not args.login_url or not args.username:
            glitch_text("Error: --login-url and --username are required in CLI mode")
            logger.error("Missing required arguments: login-url and username")
            sys.exit(1)
            
        verbose = args.verbose or not args.silent
        progress_bar = not args.no_progress
        
        # Matrix effect + spinner for CLI mode brute force as well
        result, stats = run_brute_force_attack_with_animations(
            target_url=args.login_url,
            username=args.username,
            wordlist_path=args.wordlist,
            username_field=args.username_field,
            password_field=args.password_field,
            token_fields=args.token_fields,
            success_indicator=args.success_indicator,
            delay=args.delay,
            threads=args.threads,
            proxy_path=args.proxy_path,
            csv_output=args.csv_output,
            verbose=verbose,
            progress_bar=progress_bar
        )
        
        display_attack_result(result, stats)
        
        if args.csv_output and result and result.get("success"):
            confetti_effect()
            export_results(result, stats, args.csv_output)
        elif not (result and result.get("success")):
            glitch_text("❌ No password found!")
    except KeyboardInterrupt:
        typewriter("Interrupted by user (Ctrl+C). Exiting safely...", style="bold yellow")
        sys.exit(130)
    except Exception as e:
        glitch_text(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()
