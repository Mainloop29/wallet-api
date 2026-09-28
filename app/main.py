from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import wallets


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Wallet API", lifespan=lifespan)

app.include_router(wallets.router)


@app.get("/health", tags=["service"])
async def health() -> dict[str, str]:
    return {"status": "ok"}