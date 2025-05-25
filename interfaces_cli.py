from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.console import Console
from rich.text import Text
from utils_config import VERSION, console
import json
import datetime
import os

def show_banner():
    banner = """
██████╗  ██████╗ ███████╗██╗███████╗
██╔══██╗██╔═══██╗██╔════╝██║██╔════╝
██████╔╝██║   ██║█████╗  ██║█████╗  
██╔═══╝ ██║   ██║██╔══╝  ██║██╔══╝  
██║     ╚██████╔╝██║     ██║███████╗
╚═╝      ╚═════╝ ╚═╝     ╚═╝╚══════╝
"""
    console.print(Panel(
        f"{banner}\n[bold cyan]Brute Force Toolkit v{VERSION}[/bold cyan]\n"
        "[green]Brute force tool for login[/green]",
        title="[bold magenta]ROZIE[/bold magenta]",
        border_style="magenta",
        expand=False
    ))
    console.print("[bold blue]BruteForce Audit Tool[/bold blue]")

def main_menu():
    console.print("\n[bold yellow]Main Menu[/bold yellow]")
    
    console.print("[bold]1.[/bold] Brute Force Attack")
    console.print("[bold]2.[/bold] Wordlist Generator (coming soon)")
    console.print("[bold]3.[/bold] Advanced Settings (coming soon)")
    console.print("[bold]0.[/bold] Exit")
    
    return Prompt.ask("[bold green]Choose an option[/bold green]", 
                      choices=["0", "1", "2", "3"], 
                      default="1")

def get_user_input():
    console.print("\n[bold cyan]Attack Configuration[/bold cyan]")
    
    username = Prompt.ask("[bold]Target username[/bold]")
    while not username.strip():
        console.print("[yellow]Username cannot be empty![/yellow]")
        username = Prompt.ask("[bold]Target username[/bold]")
    
    target_url = Prompt.ask("[bold]Target URL[/bold]")
    while not target_url.strip() or not (target_url.startswith("http://") or target_url.startswith("https://")):
        console.print("[yellow]Please enter a valid URL starting with http:// or https://[/yellow]")
        target_url = Prompt.ask("[bold]Target URL[/bold]")
    
    return username, target_url

def display_attack_result(result, stats=None):
    console.print("\n[bold cyan]=== Attack Result ===[/bold cyan]")
    
    if not result or not result.get("success", False):
        console.print("[red]❌ No password found.[/red]")
    else:
        console.print(f"[green]Password ditemukan: {result.get('password')}[/green]")
    
    if stats:
        console.print(f"Percobaan: {stats.get('attempts', 0)}")
        
        # Display additional statistics if available
        if 'duration' in stats:
            console.print(f"Durasi: {stats.get('duration', 0):.2f} seconds")
        if 'successes' in stats:
            console.print(f"Sukses: {stats.get('successes', 0)}")
        if 'failures' in stats:
            console.print(f"Gagal: {stats.get('failures', 0)}")

def export_results(result, stats=None, csv_output=None):
    if not result:
        return
        
    export = Prompt.ask("[bold]Export result?[/bold]", choices=["y", "n"], default="n")
    if export.lower() == "y":
        # Create results directory if it doesn't exist
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not csv_output:
            default_filename = f"attack_result_{timestamp}.json"
            csv_output = os.path.join(results_dir, default_filename)
        
        console.print(f"[cyan]Exporting results to {csv_output}...[/cyan]")
        
        # Prepare export data
        if isinstance(result, dict):
            export_data = {
                "result": {
                    "username": result.get("username"),
                    "password": result.get("password"),
                    "success": result.get("success", True)
                }
            }
        else:
            export_data = {"result": result}
            
        if stats:
            export_data["stats"] = stats
            
        # Add metadata
        export_data["metadata"] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "tool_version": VERSION
        }
            
        with open(csv_output, "w") as f:
            json.dump(export_data, f, indent=2)
            
        console.print(f"[green]Results exported to: {csv_output}[/green]")

def settings_menu():
    console.print("\n[bold yellow]Settings[/bold yellow]")
    
    settings_table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    settings_table.add_column(style="bold cyan")
    settings_table.add_column()
    
    settings_table.add_row("[1]", "Proxy Settings")
    settings_table.add_row("[2]", "Timeout Settings")
    settings_table.add_row("[3]", "User Agent Settings")
    settings_table.add_row("[4]", "Advanced Attack Options")
    settings_table.add_row("[0]", "Back to Main Menu")
    
    console.print(settings_table)
    
    return Prompt.ask("[bold green]Choose an option[/bold green]", 
                      choices=["0", "1", "2", "3", "4"], 
                      default="0")

def show_progress(current, total, status=""):
    """Display a progress bar for ongoing operations"""
    from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
    
    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(complete_style="green"),
        TaskProgressColumn(),
        TextColumn("{task.fields[status]}"),
        console=console
    ) as progress:
        task = progress.add_task(f"[cyan]Processing...", total=total, status=status)
        
        for i in range(current):
            progress.update(task, advance=1)
            # This would be replaced with actual processing in real usage
            import time
            time.sleep(0.01)
            
        progress.update(task, status=f"[green]{status}")

def confirm_action(message, default=False):
    """Ask for confirmation before proceeding with potentially dangerous actions"""
    choices = ["y", "n"]
    default_choice = "y" if default else "n"
    
    response = Prompt.ask(
        f"[bold yellow]{message}[/bold yellow]",
        choices=choices,
        default=default_choice
    )
    
    return response.lower() == "y"
