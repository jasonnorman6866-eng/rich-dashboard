"""Production-ready monitoring dashboard with Rich.

Features:
- Real-time progress tracking
- Multi-panel layout (tasks, logs, summary)
- Error handling with retry logic
- Persistent logging to file and console
"""

import time
import random
from typing import List, Dict, Optional
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn, TimeElapsedColumn
from rich.live import Live

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 0.5
UPDATE_INTERVAL = 0.5
REFRESH_RATE = 4
LOG_FILE = "dashboard.log"
LOG_RETENTION = 10

console = Console()


class TaskItem:
    """Represents a single task in the dashboard."""

    def __init__(self, email: str, company: str):
        self.email = email
        self.company = company
        self.status = "Waiting"
        self.progress = 0
        self.retries = 0
        self.started_at: Optional[datetime] = None

    def start(self) -> None:
        """Mark task as started."""
        self.status = "[bold cyan]↻ Processing[/]"
        self.started_at = datetime.now()

    def advance(self, amount: int = 20) -> None:
        """Advance task progress."""
        self.progress = min(self.progress + amount, 100)

    def complete(self) -> None:
        """Mark task as completed."""
        self.status = "[bold green]✔ Sent[/]"
        self.progress = 100

    def fail(self) -> None:
        """Mark task as failed."""
        self.status = "[bold red]✖ Failed[/]"

    def reset(self) -> None:
        """Reset task to waiting state after failure."""
        self.status = "[bold grey50]⏳ Waiting[/]"
        self.progress = 0


class Dashboard:
    """Production-ready monitoring dashboard."""

    def __init__(self, log_file: str = LOG_FILE):
        self.log_file = log_file
        self.logs: List[str] = []
        self.tasks: List[TaskItem] = []
        self.task_map: Dict[str, int] = {}
        self.progress: Optional[Progress] = None
        self._clear_log_file()

    def _clear_log_file(self) -> None:
        """Clear log file on startup."""
        with open(self.log_file, "w") as f:
            f.write(f"Dashboard started at {datetime.now().isoformat()}\n\n")

    def add_task(self, email: str, company: str) -> None:
        """Add a new task to the dashboard."""
        task = TaskItem(email, company)
        self.tasks.append(task)

    def _add_log(self, message: str) -> None:
        """Add message to logs."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.logs.append(formatted_message)

        # Keep only recent logs in memory
        if len(self.logs) > LOG_RETENTION:
            self.logs.pop(0)

        # Write to file
        with open(self.log_file, "a") as f:
            f.write(formatted_message + "\n")

    def _setup_progress(self) -> Progress:
        """Setup Rich Progress with custom columns."""
        progress = Progress(
            TextColumn("[blue]{task.fields[email]}[/]"),
            TextColumn("[yellow]{task.fields[company]}[/]"),
            TextColumn("{task.fields[status]}"),
            BarColumn(bar_width=20),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            expand=True,
        )

        for task in self.tasks:
            task_id = progress.add_task(
                description="",
                total=100,
                completed=task.progress,
                email=task.email,
                company=task.company,
                status=task.status,
            )
            self.task_map[task.email] = task_id

        return progress

    def _make_layout(self) -> Layout:
        """Create multi-panel layout."""
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

    def _render_logs(self) -> Panel:
        """Render logs panel."""
        log_text = "\n".join(self.logs[-LOG_RETENTION:]) or "No logs yet"
        return Panel(log_text, title="📋 Logs", border_style="red", expand=True)

    def _render_summary(self) -> Panel:
        """Render summary statistics panel."""
        sent = sum(1 for t in self.tasks if "Sent" in t.status)
        waiting = sum(1 for t in self.tasks if "Waiting" in t.status)
        processing = sum(1 for t in self.tasks if "Processing" in t.status)
        failed = sum(1 for t in self.tasks if "Failed" in t.status)

        summary_text = (
            f"[green]✔ Sent:[/] {sent}\n"
            f"[cyan]↻ Processing:[/] {processing}\n"
            f"[grey50]⏳ Waiting:[/] {waiting}\n"
            f"[red]✖ Failed:[/] {failed}"
        )
        return Panel(summary_text, title="📊 Summary", border_style="green")

    def _is_complete(self) -> bool:
        """Check if all tasks are complete or failed."""
        return all(
            "Sent" in t.status or "Failed" in t.status
            for t in self.tasks
        )

    def _process_tasks(self) -> None:
        """Process all tasks and update their state."""
        for task in self.tasks:
            task_id = self.task_map[task.email]

            if task.status == "[bold grey50]⏳ Waiting[/]":
                # Start task with 50% probability
                if random.random() > 0.5:
                    task.start()
                    self.progress.update(task_id, status=task.status)
                    self._add_log(f"🚀 Started task for {task.email}")

            elif "Processing" in task.status:
                # Simulate random failure (20% chance)
                if random.random() < 0.2:
                    task.retries += 1
                    if task.retries >= MAX_RETRIES:
                        task.fail()
                        self.progress.update(task_id, status=task.status)
                        self._add_log(
                            f"❌ Task failed permanently for {task.email} "
                            f"after {task.retries} retries"
                        )
                    else:
                        task.reset()
                        self.progress.update(task_id, status=task.status)
                        self._add_log(
                            f"⚠️  Task failed for {task.email}, "
                            f"retry {task.retries}/{MAX_RETRIES}"
                        )
                else:
                    # Advance progress
                    task.advance(random.choice([20, 40]))
                    self.progress.update(task_id, completed=task.progress)
                    self._add_log(f"⏳ Progress {task.progress}% for {task.email}")

                    # Complete task if progress reaches 100%
                    if task.progress >= 100:
                        task.complete()
                        self.progress.update(
                            task_id,
                            completed=100,
                            status=task.status,
                        )
                        self._add_log(f"✅ Completed task for {task.email}")

    def run(self) -> None:
        """Run the dashboard."""
        if not self.tasks:
            console.print("[red]Error: No tasks added to dashboard[/]")
            return

        self.progress = self._setup_progress()
        layout = self._make_layout()

        self._add_log(f"Dashboard initialized with {len(self.tasks)} tasks")

        try:
            with Live(layout, refresh_per_second=REFRESH_RATE, console=console):
                while not self._is_complete():
                    time.sleep(UPDATE_INTERVAL)

                    # Process all tasks
                    self._process_tasks()

                    # Update layout panels
                    layout["tasks"].update(Panel(self.progress, title="📈 Tasks"))
                    layout["logs"].update(self._render_logs())
                    layout["lower"].update(self._render_summary())

                # Show final summary
                time.sleep(1)
                self._add_log("Dashboard completed")
                final_summary = self._render_summary()
                layout["lower"].update(final_summary)

        except KeyboardInterrupt:
            self._add_log("Dashboard interrupted by user")
            console.print("\n[yellow]Dashboard interrupted[/]")
        except Exception as e:
            self._add_log(f"Dashboard error: {str(e)}")
            console.print(f"[red]Dashboard error: {str(e)}[/]")
            raise


def main() -> None:
    """Main entry point."""
    # Create dashboard
    dashboard = Dashboard()

    # Add mock tasks
    tasks = [
        ("glen.c@globalsolutions.com", "Global Solutions FL"),
        ("ryan.kennedy@acme.com", "Acme Corporation FL"),
        ("brenda.smith@sunshine.com", "Sunshine LLC Finance"),
        ("kathy.hart@pioneer.com", "Pioneer Tech FL"),
        ("mary1023@gmx.com", "Global Solutions FL"),
        ("brandon.brown@gmail.com", "Acme Corporation FL"),
        ("sea_sarah@gmx.com", "Sunshine LLC Finance"),
    ]

    for email, company in tasks:
        dashboard.add_task(email, company)

    # Run dashboard
    console.print("[bold cyan]Rich Dashboard[/] starting...")
    dashboard.run()
    console.print("[bold green]Dashboard complete![/]")


if __name__ == "__main__":
    main()
