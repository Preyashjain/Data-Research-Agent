from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.chat_routes import chat_router
from api.department_routers import department_router
from api.employee_routers import employee_router
from core.config import settings
from observability import init_langfuse

app = FastAPI(title=settings.APP_NAME, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_langfuse()

app.include_router(department_router)
app.include_router(chat_router)
app.include_router(employee_router)






