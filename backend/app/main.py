from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request
import traceback
from app.core import settings
from app.api import generation_router, export_router, images_router

# Create FastAPI app
app = FastAPI(
    title="AeroCraft API",
    description="AI-Powered Aerospace CAD Web Application",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generation_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(images_router, prefix="/api")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Read body safely for debugging (development only). Avoid logging full bodies in production.
    try:
        body_bytes = await request.body()
        body_text = body_bytes.decode('utf-8', errors='replace')
    except Exception:
        body_text = '<could not read body>'

    print(f"[VALIDATION] RequestValidationError path={request.url.path}")
    print(f"[VALIDATION] Body preview: {body_text[:200]}")
    print(f"[VALIDATION] Errors: {exc.errors()}")
    traceback.print_exc()

    # Return JSON with details but don't expose everything in production
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body_preview": body_text[:200]}
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AeroCraft API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
