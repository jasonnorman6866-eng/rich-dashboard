"""Production example: Full-featured dashboard with retries and error handling."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard import Dashboard


def main():
    """Run production dashboard example."""
    # Create dashboard
    dashboard = Dashboard()

    # Add tasks
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
    dashboard.run()


if __name__ == "__main__":
    main()
