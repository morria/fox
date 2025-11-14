"""Tests for message storage (src/message_store.py)."""

import time
from datetime import datetime, timedelta
from threading import Thread

from src.message_store import Message, MessageStore


class TestMessage:
    """Test Message class."""

    def test_message_creation(self):
        """Test creating a message with explicit timestamp."""
        timestamp = datetime(2025, 11, 13, 12, 30, 0)
        msg = Message("W1ABC", "Hello World", timestamp)

        assert msg.callsign == "W1ABC"
        assert msg.text == "Hello World"
        assert msg.timestamp == timestamp

    def test_message_creation_default_timestamp(self):
        """Test creating a message with default timestamp."""
        before = datetime.now()
        msg = Message("W1ABC", "Hello World")
        after = datetime.now()

        assert msg.callsign == "W1ABC"
        assert msg.text == "Hello World"
        assert before <= msg.timestamp <= after

    def test_message_str_formatting(self):
        """Test message string formatting."""
        timestamp = datetime(2025, 11, 13, 14, 25, 0)
        msg = Message("W1ABC", "Test message", timestamp)

        formatted = str(msg)
        assert "[14:25]" in formatted
        assert "W1ABC:" in formatted
        assert "Test message" in formatted

    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        timestamp = datetime(2025, 11, 13, 12, 30, 0)
        msg = Message("W1ABC", "Hello", timestamp)

        msg_dict = msg.to_dict()
        assert msg_dict["callsign"] == "W1ABC"
        assert msg_dict["text"] == "Hello"
        assert msg_dict["timestamp"] == timestamp.isoformat()

    def test_message_empty_text(self):
        """Test message with empty text."""
        msg = Message("W1ABC", "")
        assert msg.text == ""
        assert "W1ABC:" in str(msg)

    def test_message_special_characters(self):
        """Test message with special characters."""
        msg = Message("W1ABC", "Hello! @#$%^&*() <>")
        assert msg.text == "Hello! @#$%^&*() <>"


class TestMessageStore:
    """Test MessageStore class."""

    def test_create_message_store(self):
        """Test creating a MessageStore."""
        store = MessageStore(max_messages=10, retention_hours=12)

        assert store.max_messages == 10
        assert store.retention_hours == 12
        assert len(store._messages) == 0

    def test_create_message_store_defaults(self):
        """Test creating MessageStore with default values."""
        store = MessageStore()

        assert store.max_messages == 15
        assert store.retention_hours == 24

    def test_add_message(self):
        """Test adding a message to the store."""
        store = MessageStore()

        msg = store.add_message("W1ABC", "Test message")

        assert isinstance(msg, Message)
        assert msg.callsign == "W1ABC"
        assert msg.text == "Test message"
        assert len(store._messages) == 1

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        store = MessageStore()

        msg1 = store.add_message("W1ABC", "First")
        msg2 = store.add_message("W2DEF", "Second")
        msg3 = store.add_message("W3GHI", "Third")

        assert len(store._messages) == 3
        assert store._messages[0] == msg1
        assert store._messages[1] == msg2
        assert store._messages[2] == msg3

    def test_get_recent_messages_empty(self):
        """Test getting recent messages from empty store."""
        store = MessageStore()

        messages = store.get_recent_messages()

        assert messages == []

    def test_get_recent_messages(self, message_store, sample_messages):
        """Test getting recent messages."""
        # Add first 10 messages
        for msg in sample_messages[:10]:
            message_store._messages.append(msg)

        recent = message_store.get_recent_messages()

        # Should get all 10 since max is 15
        assert len(recent) == 10

    def test_get_recent_messages_respects_max(self, message_store, sample_messages):
        """Test that get_recent_messages respects max_messages limit."""
        # Add 20 messages
        for msg in sample_messages:
            message_store._messages.append(msg)

        recent = message_store.get_recent_messages()

        # Should only get last 15
        assert len(recent) == 15
        # Should be the most recent ones (last 15)
        assert recent[-1] == sample_messages[-1]
        assert recent[0] == sample_messages[5]  # 20 - 15 = 5

    def test_message_cleanup_on_add(self, message_store, old_message, recent_message):
        """Test that old messages are cleaned up when adding new messages."""
        # Add an old message
        message_store._messages.append(old_message)
        assert len(message_store._messages) == 1

        # Add a recent message (should trigger cleanup)
        message_store.add_message("W1NEW", "New message")

        # Old message should be removed
        messages = message_store._messages
        assert len(messages) == 1
        assert messages[0].callsign == "W1NEW"

    def test_message_cleanup_on_get(self, message_store, old_message, recent_message):
        """Test that old messages are cleaned up when getting recent messages."""
        # Manually add messages to bypass cleanup
        message_store._messages.append(old_message)
        message_store._messages.append(recent_message)
        assert len(message_store._messages) == 2

        # Get recent messages (should trigger cleanup)
        recent = message_store.get_recent_messages()

        # Should only have the recent message
        assert len(recent) == 1
        assert recent[0].callsign == "W1NEW"

    def test_retention_cutoff(self):
        """Test message retention cutoff."""
        store = MessageStore(retention_hours=1)

        # Add a message just over 1 hour old
        old_time = datetime.now() - timedelta(hours=1, minutes=1)
        old_msg = Message("W1OLD", "Old", old_time)
        store._messages.append(old_msg)

        # Add a message within 1 hour
        recent_time = datetime.now() - timedelta(minutes=30)
        recent_msg = Message("W1NEW", "New", recent_time)
        store._messages.append(recent_msg)

        # Get recent messages
        recent = store.get_recent_messages()

        # Should only have the recent message
        assert len(recent) == 1
        assert recent[0].callsign == "W1NEW"


class TestMessageStoreThreadSafety:
    """Test MessageStore thread safety."""

    def test_concurrent_add_messages(self):
        """Test adding messages from multiple threads."""
        store = MessageStore()
        num_threads = 10
        messages_per_thread = 10

        def add_messages(thread_id):
            for i in range(messages_per_thread):
                store.add_message(f"W{thread_id}ABC", f"Message {i}")

        threads = []
        for i in range(num_threads):
            thread = Thread(target=add_messages, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should have all messages
        assert len(store._messages) == num_threads * messages_per_thread

    def test_concurrent_read_write(self):
        """Test concurrent reading and writing."""
        store = MessageStore()
        stop_flag = False
        read_counts = []

        def writer():
            for i in range(50):
                store.add_message(f"W{i}ABC", f"Message {i}")
                time.sleep(0.001)

        def reader():
            count = 0
            while not stop_flag:
                _ = store.get_recent_messages()
                count += 1
                time.sleep(0.001)
            read_counts.append(count)

        # Start writer and readers
        writer_thread = Thread(target=writer)
        reader_threads = [Thread(target=reader) for _ in range(3)]

        writer_thread.start()
        for t in reader_threads:
            t.start()

        writer_thread.join()
        stop_flag = True
        for t in reader_threads:
            t.join()

        # Should have all written messages
        assert len(store._messages) == 50
        # Readers should have completed some reads
        assert all(count > 0 for count in read_counts)

    def test_concurrent_cleanup(self):
        """Test concurrent access during cleanup."""
        store = MessageStore(retention_hours=0)  # Everything expires immediately
        errors = []

        def add_and_get():
            try:
                for i in range(10):
                    store.add_message(f"W{i}ABC", f"Message {i}")
                    _ = store.get_recent_messages()
            except Exception as e:
                errors.append(e)

        threads = [Thread(target=add_and_get) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should complete without errors
        assert len(errors) == 0


class TestMessageStoreEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_max_messages_zero(self):
        """Test MessageStore with max_messages=0."""
        store = MessageStore(max_messages=0)

        store.add_message("W1ABC", "Test")
        recent = store.get_recent_messages()

        # Should return empty list
        assert recent == []

    def test_max_messages_one(self):
        """Test MessageStore with max_messages=1."""
        store = MessageStore(max_messages=1)

        store.add_message("W1ABC", "First")
        store.add_message("W2DEF", "Second")

        recent = store.get_recent_messages()

        # Should only get the last message
        assert len(recent) == 1
        assert recent[0].callsign == "W2DEF"

    def test_very_large_max_messages(self):
        """Test MessageStore with very large max_messages."""
        store = MessageStore(max_messages=10000)

        for i in range(100):
            store.add_message(f"W{i}ABC", f"Message {i}")

        recent = store.get_recent_messages()

        # Should get all 100 messages
        assert len(recent) == 100

    def test_zero_retention(self):
        """Test MessageStore with zero retention hours."""
        store = MessageStore(retention_hours=0)

        # Add messages
        store.add_message("W1ABC", "Message 1")
        time.sleep(0.01)  # Small delay to ensure time passes

        # Get recent messages (should trigger cleanup)
        recent = store.get_recent_messages()

        # All messages should be expired
        assert len(recent) == 0

    def test_very_long_message_text(self):
        """Test storing very long message text."""
        store = MessageStore()
        long_text = "A" * 10000

        msg = store.add_message("W1ABC", long_text)

        assert msg.text == long_text
        assert len(store.get_recent_messages()) == 1

    def test_unicode_in_messages(self):
        """Test storing messages with unicode characters."""
        store = MessageStore()

        msg = store.add_message("W1ABC", "Hello 世界 🌍")

        assert msg.text == "Hello 世界 🌍"
        recent = store.get_recent_messages()
        assert len(recent) == 1
        assert recent[0].text == "Hello 世界 🌍"

    def test_callsign_special_characters(self):
        """Test callsigns with special characters."""
        store = MessageStore()

        msg = store.add_message("W1ABC-15", "Test message")

        assert msg.callsign == "W1ABC-15"
        assert "[" in str(msg) and "]" in str(msg)  # Time formatting
        assert "W1ABC-15" in str(msg)
