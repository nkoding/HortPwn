# hortapi.py

import requests
from typing import Optional
import json
import logging
import os

class HortApi:
    def __init__(self, email: str, password: str, cookie_path: str = "cookie.txt"):
        self.email = email
        self.password = password
        self.cookie_path = cookie_path
        self.session = requests.Session()
        self.login_url = "https://elternportal.hortpro.de/api/user/login"
        self.base_api_url = "https://elternportal.hortpro.de/api"
        self.set_headers()
        self.load_cookies()

    def set_headers(self):
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:113.0) Gecko/20100101 Firefox/113.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "Origin": "https://elternportal.hortpro.de",
            "Connection": "keep-alive",
            "Referer": "https://elternportal.hortpro.de/login",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "TE": "trailers"
        })
        logging.debug("Set browser-like headers.")

    def load_cookies(self):
        if os.path.exists(self.cookie_path):
            try:
                with open(self.cookie_path, 'r') as f:
                    cookies = json.load(f)
                self.session.cookies.update(cookies)
                logging.info("Loaded cookies from file.")
                # Check if cookies are still valid
                if not self.check_cookies_valid():
                    logging.warning("Cookies are invalid or expired. Performing a new login.")
                    self.login()
                else:
                    logging.info("Cookies are valid.")
            except Exception as e:
                logging.error(f"Error loading cookies: {e}")
                self.login()
        else:
            self.login()

    def save_cookies(self):
        with open(self.cookie_path, 'w') as f:
            json.dump(self.session.cookies.get_dict(), f)
        logging.debug("Saved cookies.")

    def check_cookies_valid(self) -> bool:
        test_url = f"{self.base_api_url}/kids"
        response = self.session.get(test_url)
        if response.status_code == 200:
            return True
        else:
            return False

    def login(self):
        payload = {
            "email": self.email,
            "password": self.password
        }
        headers = {
            "Content-Type": "application/json"
        }
        logging.info("Attempting to log in to HortPro.")
        response = self.session.post(self.login_url, json=payload, headers=headers)
        logging.debug(f"Login Response Status Code: {response.status_code}")
        logging.debug(f"Login Response Text: {response.text}")
        if response.status_code == 200:
            cookies = self.session.cookies.get_dict()
            if 'sid-hep' in cookies:
                self.save_cookies()
                logging.info("Login successful and cookies saved.")
            else:
                logging.error("Login failed: 'sid-hep' cookie not found.")
        else:
            logging.error(f"Login failed with status code: {response.status_code}")
            logging.error(f"Response Text: {response.text}")

    def get_kid_id(self) -> Optional[str]:
        url = f"{self.base_api_url}/kids"
        logging.info(f"Retrieving kid ID from URL: {url}")
        response = self.session.get(url)
        logging.debug(f"Get Kids Response Status Code: {response.status_code}")
        logging.debug(f"Get Kids Response Text: {response.text}")
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"Get Kids Response JSON: {data}")
            if data.get("success") and data.get("data"):
                if len(data["data"]) > 0:
                    kid_id = data["data"][0].get("id")
                    logging.info(f"Found kid ID: {kid_id}")
                    return kid_id
                else:
                    logging.warning("No children found in the data.")
            else:
                logging.warning("Success not confirmed or no data available.")
        else:
            logging.error(f"Error retrieving children with status code: {response.status_code}")
            logging.error(f"Response Text: {response.text}")
        return None

    def get_presences(self, kid_id: str, start: int = 0, limit: int = 5) -> Optional[dict]:
        url = f"{self.base_api_url}/kids/{kid_id}/presences?start={start}&limit={limit}"
        logging.info(f"Retrieving presence data from URL: {url}")
        response = self.session.get(url)
        logging.debug(f"Get Presences Response Status Code: {response.status_code}")
        logging.debug(f"Get Presences Response Text: {response.text}")
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"Get Presences Response JSON: {data}")
            if data.get("success"):
                return data["data"]
        else:
            logging.error(f"Error retrieving presence data with status code: {response.status_code}")
            logging.error(f"Response Text: {response.text}")
        return None
