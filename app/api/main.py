# import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI
from fastapi.security import HTTPBearer

from app.api.middleware import authenticate_request, init_firebase
from app.api.routes import auth_route, listings_router, profile_router, users_route
from app.api.routes.listings import user_alerts
from app.schedulers.run_user_searches import notify_user_search_alerts

security = HTTPBearer()


async def lifespan(app: FastAPI):
    # Perform startup tasks
    init_firebase()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(notify_user_search_alerts, "interval", minutes=1)
    scheduler.start()
    app.state.scheduler = scheduler  # Store the scheduler in app state for access

    # TESTING
    # asyncio.create_task(notify_user_search_alerts())
    yield

    # Cleanup
    scheduler.shutdown()


app = FastAPI(dependencies=[Depends(security)], lifespan=lifespan)

app.include_router(auth_route.router)
app.include_router(users_route.router)
app.include_router(listings_router)
app.include_router(profile_router)
app.include_router(user_alerts.router)
app.middleware("http")(authenticate_request)
