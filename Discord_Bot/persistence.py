"""
Responsible for managing the persistence of the requests if the bot restarts/shuts down. Saves the requests in a JSON file.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import uuid

from config import PERSISTENCE_FILE


def load_requests() -> List[Dict]:
    if not os.path.exists(PERSISTENCE_FILE):
        return []

    try:
        with open(PERSISTENCE_FILE, "r") as f:
            data = json.load(f)
            return data.get("requests", [])
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading requests: {e}")
        return []


def save_requests(requests: List[Dict]) -> bool:
    try:
        data = {"requests": requests}
        with open(PERSISTENCE_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving requests: {e}")
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
) -> Optional[str]:
    """
    request_type: Type of request
    user_id: Discord user ID
    username: Discord username
    channel_id: Discord channel ID where notifications should be sent
    class_num: Class number
    class_subject: Class subject
    course_id: Course ID
    term: Academic term

    returns the request ID if successful, None otherwise
    """
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
        new_request["class_num"] = class_num
        new_request["class_subject"] = class_subject
    elif request_type == "course":
        new_request["course_id"] = course_id

    requests.append(new_request)

    if save_requests(requests):
        return request_id
    return None


def remove_request(request_id: str) -> bool:
    requests = load_requests()
    original_length = len(requests)

    requests = [r for r in requests if r["id"] != request_id]

    if len(requests) < original_length:
        return save_requests(requests)
    return False


def remove_user_requests(user_id: int) -> int:
    """
    Remove all tracking requests for a specific user.
    Returns the number of requests removed
    """
    requests = load_requests()
    original_length = len(requests)

    requests = [r for r in requests if r["user_id"] != user_id]

    removed_count = original_length - len(requests)
    if removed_count > 0:
        save_requests(requests)

    return removed_count


def get_user_requests(user_id: int) -> List[Dict]:
    requests = load_requests()
    return [r for r in requests if r["user_id"] == user_id]


def update_request_timestamps(
    request_id: str, last_checked: bool = False, last_notified: bool = False
) -> bool:
    """
    Update timestamp fields for a request.

    Returns true if successful, false otherwise
    """
    requests = load_requests()
    current_time = datetime.utcnow().isoformat() + "Z"

    for request in requests:
        if request["id"] == request_id:
            if last_checked:
                request["last_checked"] = current_time
            if last_notified:
                request["last_notified"] = current_time
            return save_requests(requests)

    return False


def count_user_requests(user_id: int) -> int:
    return len(get_user_requests(user_id))
