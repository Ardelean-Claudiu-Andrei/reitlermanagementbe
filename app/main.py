from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routers import (
    auth, users, products, categories, clients,
    offers, stats, parts, assemblies, quotes, projects, inventory
)

app = FastAPI(
    title="Reitler Management API",
    version="1.0.0",
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url="/redoc" if settings.APP_DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(users.router,       prefix="/api/users",       tags=["Users"])
app.include_router(products.router,    prefix="/api/products",    tags=["Products"])
app.include_router(parts.router,       prefix="/api/parts",       tags=["Parts"])
app.include_router(assemblies.router,  prefix="/api/assemblies",  tags=["Assemblies"])
app.include_router(categories.router,  prefix="/api/categories",  tags=["Categories"])
app.include_router(clients.router,     prefix="/api/clients",     tags=["Clients"])
app.include_router(quotes.router,      prefix="/api/quotes",      tags=["Quotes"])
app.include_router(projects.router,    prefix="/api/projects",    tags=["Projects"])
app.include_router(inventory.router,   prefix="/api/inventory",   tags=["Inventory"])
app.include_router(offers.router,      prefix="/api/offers",      tags=["Offers"])
app.include_router(stats.router,       prefix="/api/stats",       tags=["Stats"])


@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.APP_ENV}
