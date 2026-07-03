"""Multi-panel example: Dashboard with tasks, logs, and summary."""

import time
import random
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn, TimeElapsedColumn
from rich.live import Live

console = Console()

# Mock tasks
mock_tasks = [
    {"email": "glen.c@globalsolutions.com", "company": "Global Solutions FL", "status": "Sent", "progress": 100},
    {"email": "ryan.kennedy@acme.com", "company": "Acme Corporation FL", "status": "Sent", "progress": 100},
    {"email": "mary1023@gmx.com", "company": "Global Solutions FL", "status": "Processing", "progress": 40},
    {"email": "brandon.brown@gmail.com", "company": "Acme Corporation FL", "status": "Waiting", "progress": 0},
]

# Progress instance
progress = Progress(
    TextColumn("[blue]{task.fields[email]}[/]"),
    TextColumn("[yellow]{task.fields[company]}[/]"),
    TextColumn("{task.fields[status]}"),
    BarColumn(bar_width=20),
    TaskProgressColumn(),
    TimeElapsedColumn(),
    expand=True,
)

task_map = {}
for task in mock_tasks:
    task_id = progress.add_task(
        description="",
        total=100,
        completed=task["progress"],
        email=task["email"],
        company=task["company"],
        status=task["status"],
    )
    task_map[task["email"]] = task_id

# Layout setup
def make_layout() -> Layout:
    layout = Layout()
    layout.split(
        Layout(name="upper", ratio=3),
        Layout(name="lower", ratio=1),
    )
    layout["upper"].split_row(
        Layout(name="tasks", ratio=3),
        Layout(name="logs", ratio=2),
    )
    return layout

layout = make_layout()

# Logs and summary
logs = []

def add_log(message: str):
    logs.append(message)
    if len(logs) > 10:
        logs.pop(0)

def render_logs():
    return Panel("\n".join(logs[-10:]) or "No logs yet", title="📋 Logs", border_style="red")

def render_summary():
    sent = sum(1 for t in mock_tasks if "Sent" in t["status"])
    waiting = sum(1 for t in mock_tasks if "Waiting" in t["status"])
    processing = sum(1 for t in mock_tasks if "Processing" in t["status"])
    failed = sum(1 for t in mock_tasks if "Failed" in t["status"])
    return Panel(
        f"[green]✔ Sent:[/] {sent}\n[cyan]↻ Processing:[/] {processing}\n[grey50]⏳ Waiting:[/] {waiting}\n[red]✖ Failed:[/] {failed}",
        title="📊 Summary",
        border_style="green",
    )

# Main loop
def run_dashboard():
    with Live(layout, refresh_per_second=4, console=console):
        while any(t["status"] != "[bold green]✔ Sent[/]" for t in mock_tasks):
            time.sleep(0.5)

            for task in mock_tasks:
                task_id = task_map[task["email"]]

                if task["status"] == "Waiting":
                    if random.random() > 0.5:
                        task["status"] = "[bold cyan]↻ Processing[/]"
                        progress.update(task_id, status=task["status"])
                        add_log(f"🚀 Started task for {task['email']}")
                elif "Processing" in task["status"]:
                    task["progress"] += random.choice([20, 40])
                    progress.update(task_id, completed=task["progress"])
                    add_log(f"⏳ Progress {task['progress']}% for {task['email']}")

                    if task["progress"] >= 100:
                        task["progress"] = 100
                        task["status"] = "[bold green]✔ Sent[/]"
                        progress.update(task_id, completed=100, status=task["status"])
                        add_log(f"✅ Completed task for {task['email']}")

            # Update layout panels
            layout["tasks"].update(Panel(progress, title="📈 Tasks"))
            layout["logs"].update(render_logs())
            layout["lower"].update(render_summary())

if __name__ == "__main__":
    console.print("[bold cyan]Multi-Panel Dashboard Example[/]")
    run_dashboard()
    console.print("[bold green]Complete![/]")
