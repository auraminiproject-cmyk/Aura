import asyncio
import httpx

async def test_auth():
    base_url = "http://localhost:8000/api/v1"
    
    print("Testing signup...")
    async with httpx.AsyncClient() as client:
        # Test signup
        r = await client.post(f"{base_url}/auth/signup", json={
            "email": "test@example.com",
            "password": "securepassword",
            "display_name": "Test User"
        })
        if r.status_code == 200:
            print("Signup successful")
        elif r.status_code == 400 and "already registered" in r.text:
            print("User already exists, proceeding to login test")
        else:
            print("Signup failed:", r.status_code, r.text)

        # Test login
        print("\nTesting login...")
        r = await client.post(f"{base_url}/auth/login", json={
            "email": "test@example.com",
            "password": "securepassword"
        })
        if r.status_code == 200:
            print("Login successful")
            data = r.json()
            print("Token received:", data["access_token"][:20] + "...")
        else:
            print("Login failed:", r.status_code, r.text)

if __name__ == "__main__":
    asyncio.run(test_auth())
