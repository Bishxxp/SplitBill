from fastapi import FastAPI

app = FastAPI(
    title="SplitBill API",
    description="Shared expense management system",
    version="1.0.0"
)


@app.get("/")
def root():
    return {"message": "Welcome to SplitBill API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}