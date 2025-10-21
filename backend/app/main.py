from fastapi import FastAPI
app = FastAPI(title="UDV Team Map API")

@app.get("/health")
async def health():
    return {"status": "ok"}
