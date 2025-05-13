# import asyncio

import socketio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI
from fastapi.security import HTTPBearer

from app.api.middleware import authenticate_request, firebase_app, init_firebase
from app.api.routes import (
    auth_route,
    category_router,
    listings_router,
    profile_router,
    users_route,
)
from app.api.routes.listings import user_alerts
from app.schedulers.run_user_searches import notify_user_search_alerts

security = HTTPBearer()
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, environ, auth):
    token = auth.get("token")
    if not token:
        return False  # odmietne pripojenie
    try:
        user = auth.verify_id_token(token, firebase_app)
    except:
        return False

    sio.enter_room(sid, user["uid"])
    # všade emitni, že user je online
    await sio.emit("user_status", {"user_id": user["uid"], "is_online": True})
    return True


@sio.event
async def disconnect(sid):
    # zistiš, v ktorých miestnostiach bol
    rooms = sio.rooms(sid)
    for room in rooms:
        # vyhodenie z miestnosti
        sio.leave_room(sid, room)
        # oznámenie o offline
        await sio.emit("user_status", {"user_id": room, "is_online": False})


async def lifespan(app: FastAPI):
    # Perform startup tasks
    init_firebase()
    scheduler = AsyncIOScheduler()
    # scheduler.add_job(notify_user_search_alerts, "interval", seconds=10)
    scheduler.add_job(notify_user_search_alerts, "interval", minutes=2)

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
app.include_router(category_router)
app.middleware("http")(authenticate_request)
