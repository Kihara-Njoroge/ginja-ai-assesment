import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.config import get_settings


async def main():
    app = create_app()
    settings = get_settings()
    prefix = getattr(settings, "APP_PREFIX", "")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=f"http://test{prefix}"
    ) as client:
        r1 = await client.post(
            "/users",
            json={
                "email": "test@example.com",
                "password": "Password123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+254712345678",
            },
        )
        print("POST /users:", r1.status_code, r1.text)

        r2 = await client.post(
            "/auth/verify/request", json={"username": "nonex@example.com"}
        )
        print("POST /auth/verify/request:", r2.status_code, r2.text)


if __name__ == "__main__":
    asyncio.run(main())
