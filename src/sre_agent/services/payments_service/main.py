from fastapi import FastAPI

app = FastAPI(title="payments-service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
