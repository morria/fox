"""Message storage and retrieval for Fox BBS."""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from threading import Lock


class Message:
    """Represents a chat message."""

    def __init__(self, callsign: str, text: str, timestamp: datetime = None):
        """Initialize a message.

        Args:
            callsign: The callsign of the sender
            text: The message text
            timestamp: When the message was sent (defaults to now)
        """
        self.callsign = callsign
        self.text = text
        self.timestamp = timestamp or datetime.now()

    def __str__(self) -> str:
        """Format message for display."""
        time_str = self.timestamp.strftime("%H:%M")
        return f"[{time_str}] {self.callsign}: {self.text}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'callsign': self.callsign,
            'text': self.text,
            'timestamp': self.timestamp.isoformat()
        }


class MessageStore:
    """Stores and retrieves chat messages."""

    def __init__(self, max_messages: int = 15, retention_hours: int = 24):
        """Initialize the message store.

        Args:
            max_messages: Maximum number of messages to return
            retention_hours: How long to keep messages (in hours)
        """
        self.max_messages = max_messages
        self.retention_hours = retention_hours
        self._messages: List[Message] = []
        self._lock = Lock()

    def add_message(self, callsign: str, text: str) -> Message:
        """Add a new message to the store.

        Args:
            callsign: The callsign of the sender
            text: The message text

        Returns:
            The created message
        """
        message = Message(callsign, text)
        with self._lock:
            self._messages.append(message)
            self._cleanup_old_messages()
        return message

    def get_recent_messages(self) -> List[Message]:
        """Get recent messages within retention period.

        Returns:
            List of recent messages (up to max_messages)
        """
        with self._lock:
            self._cleanup_old_messages()
            # Return up to max_messages, most recent last
            if self.max_messages == 0:
                return []
            return self._messages[-self.max_messages:]

    def _cleanup_old_messages(self) -> None:
        """Remove messages older than retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        self._messages = [
            msg for msg in self._messages
            if msg.timestamp > cutoff_time
        ]
