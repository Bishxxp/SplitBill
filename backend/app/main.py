from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.balances import router as balances_router
from app.routers.expenses import router as expenses_router
from app.routers.groups import router as groups_router

app = FastAPI(
    title="SplitBill API",
    description="Shared expense management system",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=[
        "Content-Type",
        "X-User",
        "Idempotency-Key",
    ],
)

app.include_router(groups_router)
app.include_router(expenses_router)
app.include_router(balances_router)


@app.get("/")
def root():
    return {"message": "Welcome to SplitBill API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
