from pathlib import Path
import requests


class APIRequester:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def get(self, path=""):
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response
        except requests.RequestException:
            print("Возникла ошибка при выполнении запроса")
            return None


class SWRequester(APIRequester):
    def __init__(self, base_url="https://swapi.dev/api/"):
        super().__init__(base_url)

    def get_sw_categories(self):
        response = self.get("")
        return response.json().keys()

    def get_sw_info(self, sw_type):
        response = self.get(f"{sw_type}/")
        return response.text


def save_sw_data():
    sw = SWRequester("https://swapi.dev/api")
    categories = sw.get_sw_categories()

    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    for category in categories:
        text = sw.get_sw_info(category)
        filepath = f"data/{category}.txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)