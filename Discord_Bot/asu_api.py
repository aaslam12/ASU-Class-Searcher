"""ASU Class Search API interactions."""

import json
import logging
import re

import pandas as pd
import requests
from config import ASU_API_URL, ASU_SEARCH_URL
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger("ASU_Bot")


def scrape_course_availability(course_id: str, term: str) -> tuple:
    """Scrape course availability from ASU website using Selenium."""
    link = f"{ASU_SEARCH_URL}?campusOrOnlineSelection=A&honors=F&keywords={course_id}&promod=F&searchType=all&term={term}"

    chrome_options = Options()
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-extensions")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(link)

        wait = WebDriverWait(driver, 20)
        element = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//*[@id='class-results']"))
        )
        text = element.text
        driver.close()

        pattern = r"(\d+) of (\d+)"
        match = re.search(pattern, text)

        if match:
            enrolled = int(match.group(1))
            capacity = int(match.group(2))
            available = capacity - enrolled

            title_match = re.search(r"^(.+?)\n", text)
            title = title_match.group(1) if title_match else f"Course {course_id}"

            return enrolled, capacity, title

        return None, None, f"Course {course_id}"

    except Exception as e:
        logger.error(f"Error scraping course {course_id}: {e}")
        return None, None, f"Course {course_id}"


def check_class_via_api(class_num: str, class_subject: str, term: str) -> pd.DataFrame:
    """Check class availability via ASU API. Returns DataFrame with class info."""
    headers = {"Authorization": "Bearer null"}
    params = {
        "refine": "Y",
        "campusOrOnlineSelection": "A",
        "catalogNbr": class_num,
        "honors": "F",
        "promod": "F",
        "searchType": "all",
        "subject": class_subject,
        "term": term,
    }

    try:
        response = requests.get(ASU_API_URL, headers=headers, params=params)
        data = json.loads(response.text)
        classes_data = data.get("classes", [])

        if not classes_data:
            return pd.DataFrame()

        rows = []
        for item in classes_data:
            clas = item.get("CLAS", {})

            instructor_raw = clas.get("INSTRUCTORSLIST", "TBA")
            if isinstance(instructor_raw, list):
                instructor = ", ".join(instructor_raw) if instructor_raw else "TBA"
            else:
                instructor = instructor_raw or "TBA"

            start_time = (
                (clas.get("STARTTIME") or "")
                .replace("<br/>", "")
                .replace("&nbsp;", "")
                .strip()
            )
            end_time = (
                (clas.get("ENDTIME") or "")
                .replace("<br/>", "")
                .replace("&nbsp;", "")
                .strip()
            )
            time_str = f"{start_time}-{end_time}" if start_time else "TBA"

            enrolled = int(clas.get("ENRLTOT", 0) or 0)
            capacity = int(clas.get("ENRLCAP", 0) or 0)

            rows.append(
                {
                    "Class Name": clas.get("TITLE", "Unknown"),
                    "Instructor": instructor,
                    "Days": clas.get("DAYS") or "TBA",
                    "Time": time_str,
                    "Location": clas.get("LOCATION") or "TBA",
                    "Open Seats": capacity - enrolled,
                    "Total Seats": capacity,
                    "Enrolled": enrolled,
                }
            )

        return pd.DataFrame(rows)

    except Exception as e:
        logger.error(f"API error checking {class_subject} {class_num}: {e}")
        return pd.DataFrame()


def get_class_details(class_num: str, class_subject: str, term: str) -> dict:
    """Get full details of a class from ASU API."""
    try:
        df = check_class_via_api(class_num, class_subject, term)
        if not df.empty:
            return {
                "title": df["Class Name"].iloc[0],
                "instructor": df["Instructor"].iloc[0],
                "days": df["Days"].iloc[0],
                "time": df["Time"].iloc[0],
                "location": df["Location"].iloc[0],
            }
    except Exception as e:
        logger.error(f"Error getting class details: {e}")

    return {}


def search_classes_by_subject(
    subject: str, term: str = "2261", course_num: str = None
) -> list:
    """Search for classes by subject code, with optional course number filter."""
    headers = {"Authorization": "Bearer null"}
    params = {
        "refine": "Y",
        "campusOrOnlineSelection": "A",
        "honors": "F",
        "promod": "F",
        "searchType": "all",
        "subject": subject.upper(),
        "term": term,
    }

    if course_num:
        params["catalogNbr"] = course_num

    try:
        all_classes = []
        response = requests.get(ASU_API_URL, headers=headers, params=params)
        data = json.loads(response.text)
        all_classes.extend(data.get("classes", []))

        # API returns max 200 at a time
        scroll_id = data.get("scrollId")
        total = data.get("total", {}).get("value", 0)

        while scroll_id and len(all_classes) < total and not course_num:
            params["scrollId"] = scroll_id
            response = requests.get(ASU_API_URL, headers=headers, params=params)
            data = json.loads(response.text)
            new_classes = data.get("classes", [])
            if not new_classes:
                break
            all_classes.extend(new_classes)
            scroll_id = data.get("scrollId")

        return [_parse_class_info(item) for item in all_classes]

    except Exception as e:
        logger.error(f"Error searching classes: {e}")
        return []


def _parse_class_info(item: dict) -> dict:
    """Parse raw API class data into clean dict."""
    clas = item.get("CLAS", {})

    instructor_raw = clas.get("INSTRUCTORSLIST", "TBA")
    if isinstance(instructor_raw, list):
        instructor = ", ".join(instructor_raw) if instructor_raw else "TBA"
    else:
        instructor = instructor_raw or "TBA"

    start_time = (
        (clas.get("STARTTIME") or "").replace("<br/>", "").replace("&nbsp;", "").strip()
    )
    end_time = (
        (clas.get("ENDTIME") or "").replace("<br/>", "").replace("&nbsp;", "").strip()
    )

    enrolled = int(clas.get("ENRLTOT", 0) or 0)
    capacity = int(clas.get("ENRLCAP", 0) or 0)

    return {
        "catalog_num": clas.get("CATALOGNBR", "N/A"),
        "title": clas.get("TITLE", "N/A"),
        "enrolled": enrolled,
        "capacity": capacity,
        "available": capacity - enrolled,
        "instructor": instructor,
        "days": clas.get("DAYS") or "TBA",
        "time": f"{start_time}-{end_time}" if start_time else "TBA",
        "location": clas.get("LOCATION") or "TBA",
        "class_nbr": clas.get("CLASSNBR", "N/A"),
    }
