import requests
from typing import Dict, Any, List
from config import config

class APIClient:
    def __init__(self):
        self.base_url = config.BASE_URL
        self.token = config.TOKEN
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def search(self, db_name: str, query: str, expr: str = None) -> Dict[str, Any]:
        """调用 /search 接口"""
        url = f"{self.base_url}/databases/{db_name}/search"
        payload = {
            "token": self.token,
            "query": query,
            "top_k": config.TOP_K,
            "metric_type": config.DEFAULT_METRIC_TYPE,
        }
        if expr:
            payload["expr"] = expr

        resp = self.session.post(url, json=payload)
        if resp.status_code != 200:
            raise Exception(f"Search API error: {resp.text}")
        return resp.json()

    def dialogue(self, user_input: str) -> str:
        """调用 /dialogue 接口"""
        url = f"{self.base_url}/dialogue"
        payload = {"user_input": user_input, 
                   "token": self.token,
                   "max_tokens": 1024
                   }
        resp = self.session.post(url, json=payload)
        if resp.status_code != 200:
            raise Exception(f"Dialogue API error: {resp.text}")
        return resp.json().get("response", "")