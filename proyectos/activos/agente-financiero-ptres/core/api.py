from fastapi import FastAPI

app = FastAPI(title="Agente Financiero P3")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
