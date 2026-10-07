from pathlib import Path

import pytest
import requests
import requests_mock

import swapi


class TestAPIRequester:
    def test_init_removes_trailing_slash(self):
        requester = swapi.APIRequester("https://swapi.dev/api/")

        assert requester.base_url == "https://swapi.dev/api"

    def test_get_success(self):
        requester = swapi.APIRequester("https://example.com")

        with requests_mock.Mocker() as mock:
            mock.get(
                "https://example.com/test",
                json={"status": "ok"},
            )

            response = requester.get("test")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_get_error_returns_none(self, capsys):
        requester = swapi.APIRequester("https://example.com")

        with requests_mock.Mocker() as mock:
            mock.get(
                "https://example.com/test",
                exc=requests.RequestException,
            )

            response = requester.get("test")

        captured = capsys.readouterr()

        assert response is None
        assert "Возникла ошибка при выполнении запроса" in captured.out


class TestSWRequester:
    def test_get_sw_categories(self):
        requester = swapi.SWRequester("https://swapi.dev/api")

        with requests_mock.Mocker() as mock:
            mock.get(
                "https://swapi.dev/api/",
                json={
                    "people": "https://swapi.dev/api/people/",
                    "planets": "https://swapi.dev/api/planets/",
                },
            )

            categories = requester.get_sw_categories()

        assert list(categories) == ["people", "planets"]

    def test_get_sw_info_single_page(self):
        requester = swapi.SWRequester("https://swapi.dev/api")

        with requests_mock.Mocker() as mock:
            mock.get(
                "https://swapi.dev/api/people/",
                json={
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {"name": "Luke Skywalker"},
                        {"name": "Darth Vader"},
                    ],
                },
            )

            result = requester.get_sw_info("people")

        assert result == [
            {"name": "Luke Skywalker"},
            {"name": "Darth Vader"},
        ]

    def test_get_sw_info_pagination(self):
        requester = swapi.SWRequester("https://swapi.dev/api")

        with requests_mock.Mocker() as mock:
            mock.get(
                "https://swapi.dev/api/people/",
                json={
                    "next": "https://swapi.dev/api/people/?page=2",
                    "results": [
                        {"name": "Luke Skywalker"},
                        {"name": "Darth Vader"},
                    ],
                },
            )

            mock.get(
                "https://swapi.dev/api/people/?page=2",
                json={
                    "next": None,
                    "results": [
                        {"name": "Leia Organa"},
                    ],
                },
            )

            result = requester.get_sw_info("people")

        assert result == [
            {"name": "Luke Skywalker"},
            {"name": "Darth Vader"},
            {"name": "Leia Organa"},
        ]

    def test_get_sw_info_stops_on_request_error(self):
        requester = swapi.SWRequester("https://swapi.dev/api")

        with requests_mock.Mocker() as mock:
            mock.get(
                "https://swapi.dev/api/people/",
                exc=requests.RequestException,
            )

            result = requester.get_sw_info("people")

        assert result == []


class TestSaveSWData:
    def test_save_sw_data(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        class MockSWRequester:
            def __init__(self, base_url):
                self.base_url = base_url

            def get_sw_categories(self):
                return ["people", "planets"]

            def get_sw_info(self, category):
                return [{"category": category}]

        monkeypatch.setattr(swapi, "SWRequester", MockSWRequester)

        swapi.save_sw_data()

        people_file = Path("data/people.json")
        planets_file = Path("data/planets.json")

        assert people_file.exists()
        assert planets_file.exists()

        assert '"category": "people"' in people_file.read_text(
            encoding="utf-8"
        )
        assert '"category": "planets"' in planets_file.read_text(
            encoding="utf-8"
        )