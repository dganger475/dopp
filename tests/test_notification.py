"""Notification Model Tests
======================

Tests for the Notification model functionality, including:
- Notification creation
- Notification retrieval
- Notification marking as read
- Notification deletion
"""

import pytest
from datetime import datetime
from models.social.notification import Notification
from models.user import User
from utils.db.database import get_users_db_connection

@pytest.fixture
def test_notification(app, test_user):
    with app.app_context():
        notification = Notification.create(user_id=test_user.id, notification_type="like", content="Test notification")
        yield notification
        notification.delete()


def test_notification_creation(app, test_user):
    with app.app_context():
        notification = Notification.create(user_id=test_user.id, notification_type="like", content="Test notification")
        assert notification is not None
        assert notification.user_id == test_user.id
        assert notification.notification_type == "like"
        assert notification.content == "Test notification"
        notification.delete()


def test_notification_retrieval(app, test_user):
    with app.app_context():
        notification = Notification.create(user_id=test_user.id, notification_type="like", content="Test notification")
        retrieved_notification = Notification.get_by_id(notification.id)
        assert retrieved_notification is not None
        assert retrieved_notification.id == notification.id
        assert retrieved_notification.user_id == notification.user_id
        assert retrieved_notification.notification_type == notification.notification_type
        assert retrieved_notification.content == notification.content
        notification.delete()


def test_notification_marking_as_read(app, test_user):
    with app.app_context():
        notification = Notification.create(user_id=test_user.id, notification_type="like", content="Test notification")
        notification.mark_as_read()
        assert notification.read_at is not None
        notification.delete()


def test_notification_deletion(app, test_user):
    with app.app_context():
        notification = Notification.create(user_id=test_user.id, notification_type="like", content="Test notification")
        notification_id = notification.id
        notification.delete()
        deleted_notification = Notification.get_by_id(notification_id)
        assert deleted_notification is None


def test_notification_ordering(app, test_user):
    with app.app_context():
        notification1 = Notification.create(user_id=test_user.id, notification_type="like", content="Test notification 1")
        notification2 = Notification.create(user_id=test_user.id, notification_type="like", content="Test notification 2")
        notifications = Notification.get_by_user_id(test_user.id)
        assert len(notifications) == 2
        assert notifications[0].id == notification2.id
        assert notifications[1].id == notification1.id
        notification1.delete()
        notification2.delete()


def test_notification_pagination(app, test_user):
    with app.app_context():
        notifications = []
        for i in range(25):
            notification = Notification.create(user_id=test_user.id, notification_type="like", content=f"Test notification {i}")
            notifications.append(notification)
        first_page = Notification.get_by_user_id(test_user.id, page=1, per_page=10)
        assert len(first_page) == 10
        second_page = Notification.get_by_user_id(test_user.id, page=2, per_page=10)
        assert len(second_page) == 10
        third_page = Notification.get_by_user_id(test_user.id, page=3, per_page=10)
        assert len(third_page) == 5
        for notification in notifications:
            notification.delete()


def test_user_notifications(app, test_user):
    with app.app_context():
        notification = Notification.create(user_id=test_user.id, notification_type="like", content="Test notification")
        notifications = Notification.get_by_user_id(test_user.id)
        assert len(notifications) == 1
        assert notifications[0].id == notification.id
        notification.delete()

def test_notification_ordering(self):
    """Test notification ordering."""
    # Create notifications with different timestamps
    for i in range(3):
        Notification.create(
            user_id=self.user1.id,
            type="like",
            data={"post_id": i, "user_id": self.user2.id}
        )
    
    # Get notifications
    notifications = Notification.get_for_user(self.user1.id)
    
    # Verify they are ordered by created_at in descending order
    for i in range(len(notifications) - 1):
        current_time = datetime.strptime(notifications[i].created_at, "%Y-%m-%d %H:%M:%S")
        next_time = datetime.strptime(notifications[i + 1].created_at, "%Y-%m-%d %H:%M:%S")
        self.assertGreaterEqual(current_time, next_time)

def test_notification_pagination(self):
    """Test notification pagination."""
    # Create multiple notifications
    for i in range(10):
        Notification.create(
            user_id=self.user1.id,
            type="like",
            data={"post_id": i, "user_id": self.user2.id}
        )
    
    # Get first page
    notifications1 = Notification.get_for_user(self.user1.id, limit=5, offset=0)
    self.assertIsNotNone(notifications1)
    self.assertLessEqual(len(notifications1), 5)
    
    # Get second page
    notifications2 = Notification.get_for_user(self.user1.id, limit=5, offset=5)
    self.assertIsNotNone(notifications2)
    self.assertLessEqual(len(notifications2), 5)
    
    # Verify no overlap
    notification1_ids = {n.id for n in notifications1}
    notification2_ids = {n.id for n in notifications2}
    self.assertEqual(len(notification1_ids.intersection(notification2_ids)), 0)

if __name__ == '__main__':
    pytest.main() 