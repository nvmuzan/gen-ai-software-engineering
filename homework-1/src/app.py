import uvicorn
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.limiter import limiter
from src.routes.accounts import router as accounts_router
from src.routes.transactions import router as transactions_router

app = FastAPI(
    title="Banking Transactions API",
    description="Simple REST API for banking transactions with in-memory storage.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(transactions_router)
app.include_router(accounts_router)


if __name__ == "__main__":
    uvicorn.run("src.app:app", host="0.0.0.0", port=3000, reload=True)
