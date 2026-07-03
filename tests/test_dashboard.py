"""Unit tests for Dashboard class."""

import pytest
import os
import tempfile
from dashboard import Dashboard, TaskItem


class TestTaskItem:
    """Tests for TaskItem class."""

    def test_task_creation(self):
        """Test task creation."""
        task = TaskItem("test@example.com", "Test Company")
        assert task.email == "test@example.com"
        assert task.company == "Test Company"
        assert task.status == "Waiting"
        assert task.progress == 0
        assert task.retries == 0

    def test_task_start(self):
        """Test task start."""
        task = TaskItem("test@example.com", "Test Company")
        task.start()
        assert "Processing" in task.status
        assert task.started_at is not None

    def test_task_advance(self):
        """Test task progress advance."""
        task = TaskItem("test@example.com", "Test Company")
        task.advance(20)
        assert task.progress == 20
        task.advance(30)
        assert task.progress == 50

    def test_task_advance_max(self):
        """Test task progress cannot exceed 100."""
        task = TaskItem("test@example.com", "Test Company")
        task.advance(150)
        assert task.progress == 100

    def test_task_complete(self):
        """Test task completion."""
        task = TaskItem("test@example.com", "Test Company")
        task.complete()
        assert "Sent" in task.status
        assert task.progress == 100

    def test_task_fail(self):
        """Test task failure."""
        task = TaskItem("test@example.com", "Test Company")
        task.fail()
        assert "Failed" in task.status

    def test_task_reset(self):
        """Test task reset after failure."""
        task = TaskItem("test@example.com", "Test Company")
        task.start()
        task.fail()
        task.reset()
        assert "Waiting" in task.status
        assert task.progress == 0


class TestDashboard:
    """Tests for Dashboard class."""

    @pytest.fixture
    def temp_log_file(self):
        """Create temporary log file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_dashboard_creation(self, temp_log_file):
        """Test dashboard creation."""
        dashboard = Dashboard(log_file=temp_log_file)
        assert dashboard.log_file == temp_log_file
        assert len(dashboard.tasks) == 0
        assert len(dashboard.logs) == 0

    def test_add_task(self, temp_log_file):
        """Test adding tasks to dashboard."""
        dashboard = Dashboard(log_file=temp_log_file)
        dashboard.add_task("test@example.com", "Test Company")
        assert len(dashboard.tasks) == 1
        assert dashboard.tasks[0].email == "test@example.com"
        assert dashboard.tasks[0].company == "Test Company"

    def test_add_multiple_tasks(self, temp_log_file):
        """Test adding multiple tasks."""
        dashboard = Dashboard(log_file=temp_log_file)
        for i in range(5):
            dashboard.add_task(f"user{i}@example.com", f"Company {i}")
        assert len(dashboard.tasks) == 5

    def test_log_file_creation(self, temp_log_file):
        """Test that log file is created."""
        dashboard = Dashboard(log_file=temp_log_file)
        assert os.path.exists(temp_log_file)

    def test_add_log(self, temp_log_file):
        """Test adding log messages."""
        dashboard = Dashboard(log_file=temp_log_file)
        dashboard._add_log("Test log message")
        assert len(dashboard.logs) == 1
        assert "Test log message" in dashboard.logs[0]

    def test_log_retention(self, temp_log_file):
        """Test log retention limit."""
        from dashboard import LOG_RETENTION
        dashboard = Dashboard(log_file=temp_log_file)
        for i in range(LOG_RETENTION + 5):
            dashboard._add_log(f"Message {i}")
        assert len(dashboard.logs) <= LOG_RETENTION

    def test_render_logs(self, temp_log_file):
        """Test log rendering."""
        dashboard = Dashboard(log_file=temp_log_file)
        dashboard._add_log("Test message 1")
        dashboard._add_log("Test message 2")
        logs_panel = dashboard._render_logs()
        assert logs_panel is not None

    def test_is_complete_empty(self, temp_log_file):
        """Test completion check with empty dashboard."""
        dashboard = Dashboard(log_file=temp_log_file)
        assert dashboard._is_complete()

    def test_is_complete_with_waiting_tasks(self, temp_log_file):
        """Test completion check with waiting tasks."""
        dashboard = Dashboard(log_file=temp_log_file)
        dashboard.add_task("test@example.com", "Test Company")
        assert not dashboard._is_complete()

    def test_is_complete_with_sent_tasks(self, temp_log_file):
        """Test completion check with sent tasks."""
        dashboard = Dashboard(log_file=temp_log_file)
        task = TaskItem("test@example.com", "Test Company")
        task.complete()
        dashboard.tasks.append(task)
        assert dashboard._is_complete()

    def test_is_complete_with_failed_tasks(self, temp_log_file):
        """Test completion check with failed tasks."""
        dashboard = Dashboard(log_file=temp_log_file)
        task = TaskItem("test@example.com", "Test Company")
        task.fail()
        dashboard.tasks.append(task)
        assert dashboard._is_complete()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
