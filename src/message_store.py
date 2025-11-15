"""Message storage and retrieval for Fox BBS."""

from collections import deque
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional


class Message:
    """Represents a chat message."""

    def __init__(self, callsign: str, text: str, timestamp: Optional[datetime] = None):
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
            "callsign": self.callsign,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
        }


class MessageStore:
    """Stores and retrieves chat messages.

    Uses a bounded deque for efficient O(1) operations and automatic memory management.
    """

    def __init__(self, max_messages: int = 15, retention_hours: int = 24):
        """Initialize the message store.

        Args:
            max_messages: Maximum number of messages to store (older messages auto-dropped)
            retention_hours: Kept for compatibility, not actively used (deque handles retention)
        """
        self.max_messages = max_messages
        # retention_hours kept for backward compatibility but not used
        # deque automatically drops oldest when maxlen is reached
        self._messages: deque = deque(maxlen=max_messages if max_messages > 0 else None)
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
            self._messages.append(message)  # O(1) - auto-drops oldest if at maxlen
        return message

    def get_recent_messages(self) -> List[Message]:
        """Get recent messages.

        Returns:
            List of recent messages (up to max_messages)
        """
        with self._lock:
            return list(self._messages)  # Returns all messages in deque
