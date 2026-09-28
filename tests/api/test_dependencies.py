from httpx import AsyncClient

from app.config import AppConfig

URL = "/api/v1/user/1/recommend?query_param=5"


class TestRequireBearer:
    async def test_auth_disabled_passes_without_header(self, test_config: AppConfig, test_client: AsyncClient) -> None:
        ## GIVEN: cfg with no api_token (auth disabled)
        test_config.api_token = None

        ## WHEN: GET a protected route with no Authorization header
        response = await test_client.get(URL)

        ## THEN: 200
        assert response.status_code == 200

    async def test_missing_credentials_returns_401(self, test_config: AppConfig, test_client: AsyncClient) -> None:
        ## GIVEN: cfg with an api_token set
        test_config.api_token = "secret123"

        ## WHEN: GET a protected route with no Authorization header
        response = await test_client.get(URL)

        ## THEN: 401 with the expected detail
        assert response.status_code == 401
        assert response.json() == {"detail": "Missing bearer token"}

    async def test_wrong_token_returns_401(self, test_config: AppConfig, test_client: AsyncClient) -> None:
        ## GIVEN: cfg with an api_token set
        test_config.api_token = "secret123"

        ## WHEN: GET a protected route with a wrong bearer token
        response = await test_client.get(URL, headers={"Authorization": "Bearer wrong"})

        ## THEN: 401 with the expected detail
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid bearer token"}

    async def test_correct_token_returns_200(self, test_config: AppConfig, test_client: AsyncClient) -> None:
        ## GIVEN: cfg with an api_token set
        test_config.api_token = "secret123"

        ## WHEN: GET a protected route with the correct bearer token
        response = await test_client.get(URL, headers={"Authorization": "Bearer secret123"})

        ## THEN: 200
        assert response.status_code == 200
