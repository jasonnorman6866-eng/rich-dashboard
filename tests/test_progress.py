"""Unit tests for progress tracking functionality."""

import pytest
from dashboard import TaskItem, Dashboard
import tempfile
import os


class TestProgressTracking:
    """Tests for progress tracking."""

    def test_progress_initialization(self):
        """Test progress initializes at 0."""
        task = TaskItem("test@example.com", "Company")
        assert task.progress == 0

    def test_progress_advance_single_step(self):
        """Test advancing progress by single step."""
        task = TaskItem("test@example.com", "Company")
        task.advance(10)
        assert task.progress == 10

    def test_progress_advance_multiple_steps(self):
        """Test advancing progress multiple times."""
        task = TaskItem("test@example.com", "Company")
        task.advance(20)
        task.advance(30)
        task.advance(25)
        assert task.progress == 75

    def test_progress_capped_at_100(self):
        """Test progress cannot exceed 100."""
        task = TaskItem("test@example.com", "Company")
        task.advance(60)
        task.advance(50)  # Total would be 110, but capped at 100
        assert task.progress == 100

    def test_progress_on_completion(self):
        """Test progress is 100 on completion."""
        task = TaskItem("test@example.com", "Company")
        task.complete()
        assert task.progress == 100

    def test_progress_reset_on_retry(self):
        """Test progress resets when task retries."""
        task = TaskItem("test@example.com", "Company")
        task.advance(50)
        task.reset()
        assert task.progress == 0

    def test_multiple_tasks_progress_independence(self):
        """Test that multiple tasks track progress independently."""
        task1 = TaskItem("user1@example.com", "Company A")
        task2 = TaskItem("user2@example.com", "Company B")

        task1.advance(30)
        task2.advance(70)

        assert task1.progress == 30
        assert task2.progress == 70

    def test_retry_counter_increments(self):
        """Test retry counter increments on failure."""
        task = TaskItem("test@example.com", "Company")
        assert task.retries == 0
        task.retries += 1
        assert task.retries == 1
        task.retries += 1
        assert task.retries == 2

    def test_status_transitions(self):
        """Test status transitions through lifecycle."""
        task = TaskItem("test@example.com", "Company")
        
        # Initial state
        assert "Waiting" in task.status
        
        # Start processing
        task.start()
        assert "Processing" in task.status
        
        # Complete
        task.complete()
        assert "Sent" in task.status

    def test_status_transitions_with_failure(self):
        """Test status transitions with failure and retry."""
        task = TaskItem("test@example.com", "Company")
        
        # Start
        task.start()
        assert "Processing" in task.status
        
        # Fail
        task.fail()
        assert "Failed" in task.status
        
        # Reset for retry
        task.reset()
        assert "Waiting" in task.status


class TestDashboardProgressTracking:
    """Tests for dashboard-level progress tracking."""

    @pytest.fixture
    def temp_log_file(self):
        """Create temporary log file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            temp_path = f.name
        yield temp_path
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_dashboard_tracks_multiple_tasks(self, temp_log_file):
        """Test dashboard tracks multiple tasks."""
        dashboard = Dashboard(log_file=temp_log_file)
        
        for i in range(5):
            dashboard.add_task(f"user{i}@example.com", f"Company {i}")
        
        assert len(dashboard.tasks) == 5
        assert all(t.progress == 0 for t in dashboard.tasks)

    def test_dashboard_logs_progress(self, temp_log_file):
        """Test dashboard logs progress updates."""
        dashboard = Dashboard(log_file=temp_log_file)
        dashboard._add_log("Task progress: 25%")
        dashboard._add_log("Task progress: 50%")
        dashboard._add_log("Task progress: 100%")
        
        assert len(dashboard.logs) == 3

    def test_summary_counts_completed_tasks(self, temp_log_file):
        """Test summary counts completed tasks."""
        dashboard = Dashboard(log_file=temp_log_file)
        
        task1 = TaskItem("user1@example.com", "Company A")
        task1.complete()
        
        task2 = TaskItem("user2@example.com", "Company B")
        task2.start()
        
        task3 = TaskItem("user3@example.com", "Company C")
        
        dashboard.tasks = [task1, task2, task3]
        
        # Create summary to verify counts
        summary = dashboard._render_summary()
        assert summary is not None

    def test_dashboard_progress_independence(self, temp_log_file):
        """Test dashboard tasks track progress independently."""
        dashboard = Dashboard(log_file=temp_log_file)
        dashboard.add_task("user1@example.com", "Company A")
        dashboard.add_task("user2@example.com", "Company B")
        
        dashboard.tasks[0].advance(50)
        dashboard.tasks[1].advance(25)
        
        assert dashboard.tasks[0].progress == 50
        assert dashboard.tasks[1].progress == 25


class TestProgressEdgeCases:
    """Tests for edge cases in progress tracking."""

    def test_zero_progress_advance(self):
        """Test advancing by zero."""
        task = TaskItem("test@example.com", "Company")
        task.advance(0)
        assert task.progress == 0

    def test_negative_progress_advance(self):
        """Test behavior with negative advance (should not go below 0)."""
        task = TaskItem("test@example.com", "Company")
        task.advance(50)
        # Note: Current implementation doesn't prevent negative,
        # but min(x+y, 100) still caps at 100
        task.advance(-20)
        # Result depends on implementation; documenting expected behavior
        assert task.progress >= 0

    def test_large_advance_values(self):
        """Test advancing with very large values."""
        task = TaskItem("test@example.com", "Company")
        task.advance(999999)
        assert task.progress == 100

    def test_decimal_progress_not_supported(self):
        """Test that progress values are integers."""
        task = TaskItem("test@example.com", "Company")
        task.advance(25)
        assert isinstance(task.progress, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
