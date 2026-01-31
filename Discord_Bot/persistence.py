"""Persistence layer for tracking requests. Saves data to JSON file."""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from config import PERSISTENCE_FILE


def load_requests() -> List[Dict]:
    if not os.path.exists(PERSISTENCE_FILE):
        return []

    try:
        with open(PERSISTENCE_FILE, "r") as f:
            data = json.load(f)
            return data.get("requests", [])
    except (json.JSONDecodeError, IOError):
        return []


def save_requests(requests: List[Dict]) -> bool:
    try:
        with open(PERSISTENCE_FILE, "w") as f:
            json.dump({"requests": requests}, f, indent=2)
        return True
    except IOError:
        return False


def add_request(
    request_type: str,
    user_id: int,
    username: str,
    channel_id: int,
    class_num: str = None,
    class_subject: str = None,
    course_id: str = None,
    term: str = None,
    class_title: str = None,
    class_details: dict = None,
) -> Optional[str]:
    """Add a new tracking request. Returns request ID if successful."""
    requests = load_requests()
    request_id = str(uuid.uuid4())

    new_request = {
        "id": request_id,
        "type": request_type,
        "user_id": user_id,
        "username": username,
        "channel_id": channel_id,
        "term": term,
        "added_at": datetime.utcnow().isoformat() + "Z",
        "last_checked": None,
        "last_notified": None,
    }

    if request_type == "class":
        new_request.update(
            {
                "class_num": class_num,
                "class_subject": class_subject,
                "class_title": class_title or "Unknown",
            }
        )
        if class_details:
            new_request.update(
                {
                    "instructor": class_details.get("instructor", "TBA"),
                    "days": class_details.get("days", "TBA"),
                    "time": class_details.get("time", "TBA"),
                    "location": class_details.get("location", "TBA"),
                }
            )

    elif request_type == "course":
        new_request.update(
            {
                "course_id": course_id,
                "course_title": class_title or "Unknown",
            }
        )
        if class_details:
            new_request.update(
                {
                    "instructor": class_details.get("instructor", "TBA"),
                    "days": class_details.get("days", "TBA"),
                    "time": class_details.get("time", "TBA"),
                    "location": class_details.get("location", "TBA"),
                }
            )

    requests.append(new_request)
    return request_id if save_requests(requests) else None


def remove_request(request_id: str) -> bool:
    """Remove a request by ID."""
    requests = load_requests()
    original_length = len(requests)
    requests = [r for r in requests if r["id"] != request_id]

    if len(requests) < original_length:
        return save_requests(requests)
    return False


def remove_user_requests(user_id: int) -> int:
    """Remove all requests for a user. Returns count removed."""
    requests = load_requests()
    original_length = len(requests)
    requests = [r for r in requests if r["user_id"] != user_id]

    removed_count = original_length - len(requests)
    if removed_count > 0:
        save_requests(requests)
    return removed_count


def get_user_requests(user_id: int) -> List[Dict]:
    """Get all requests for a specific user."""
    return [r for r in load_requests() if r["user_id"] == user_id]


def count_user_requests(user_id: int) -> int:
    """Count requests for a specific user."""
    return len(get_user_requests(user_id))


def update_request(request_id: str, updates: Dict) -> bool:
    """Update fields on a request."""
    requests = load_requests()

    for request in requests:
        if request["id"] == request_id:
            request.update(updates)
            return save_requests(requests)

    return False


def is_duplicate_request(
    user_id: int,
    request_type: str,
    class_num: str = None,
    class_subject: str = None,
    course_id: str = None,
    term: str = None,
) -> bool:
    """Check if user already has an identical tracking request."""
    for request in get_user_requests(user_id):
        if request["type"] != request_type or request["term"] != term:
            continue

        if request_type == "class":
            if (
                request.get("class_num") == class_num
                and request.get("class_subject") == class_subject
            ):
                return True

        elif request_type == "course":
            if request.get("course_id") == course_id:
                return True

    return False
