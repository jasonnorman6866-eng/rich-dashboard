"""Basic example: Simple progress bar with Rich."""

import time
from rich.progress import Progress


def main():
    """Run basic progress example."""
    print("[Basic Progress Bar Example]\n")

    with Progress() as progress:
        task = progress.add_task("[cyan]Processing...", total=100)

        while not progress.finished:
            progress.update(task, advance=5)
            time.sleep(0.1)

    print("\n✅ Complete!")


if __name__ == "__main__":
    main()
