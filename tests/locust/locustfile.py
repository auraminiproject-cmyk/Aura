from locust import HttpUser, between, task


class FashionAIUser(HttpUser):
    wait_time = between(1, 3)
    token: str | None = None

    def on_start(self):
        r = self.client.post("/api/v1/auth/guest", json={"display_name": "LoadTest"})
        if r.ok:
            self.token = r.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(3)
    def health(self):
        self.client.get("/health")

    @task(2)
    def chat(self):
        if not self.token:
            return
        self.client.post(
            "/api/v1/chat/message",
            json={"message": "wedding red saree 5000", "language": "te"},
        )

    @task(1)
    def search(self):
        if not self.token:
            return
        self.client.post("/api/v1/search/products", json={"query": "red lehenga wedding"})
