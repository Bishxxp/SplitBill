from fastapi import FastAPI

from app.routers.balances import router as balances_router
from app.routers.expenses import router as expenses_router
from app.routers.groups import router as groups_router

app = FastAPI(
    title="SplitBill API",
    description="Shared expense management system",
    version="1.0.0",
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