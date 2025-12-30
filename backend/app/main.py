"""
Suraksh Backend API - Main Entry Point
FastAPI application with strict typing and Zero Trust security patterns.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # #region agent log
        import json
        try:
            with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
                f.write(json.dumps({"location":"main.py:RequestLoggingMiddleware","message":"Incoming request","data":{"method":request.method,"path":str(request.url.path),"origin":request.headers.get("origin"),"host":request.headers.get("host")},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"A,C"}) + '\n')
        except: pass
        # #endregion
        response = await call_next(request)
        # #region agent log
        try:
            with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
                f.write(json.dumps({"location":"main.py:RequestLoggingMiddleware","message":"Request completed","data":{"status":response.status_code,"path":str(request.url.path)},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"A,C"}) + '\n')
        except: pass
        # #endregion
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    print("[STARTUP] Suraksh Backend API starting up...")
    
    # Initialize Neo4j connection (Phase 2 - optional for Phase 1)
    try:
        from app.core.database import get_neo4j_driver, verify_neo4j_connection
        driver = get_neo4j_driver()
        if await verify_neo4j_connection():
            print("[OK] Neo4j connection verified")
        else:
            print("[WARN] Neo4j connection verification failed")
    except Exception as e:
        print(f"[WARN] Failed to initialize Neo4j: {e}")
        print("   Graph operations may fail until Neo4j is available")
    
    # Initialize Qdrant connection (Phase 2 - optional for Phase 1)
    try:
        from app.core.database import get_qdrant_client, ensure_qdrant_collection, verify_qdrant_connection
        client = get_qdrant_client()
        await ensure_qdrant_collection()
        if await verify_qdrant_connection():
            print("[OK] Qdrant connection verified")
        else:
            print("[WARN] Qdrant connection verification failed")
    except Exception as e:
        print(f"[WARN] Failed to initialize Qdrant: {e}")
        print("   Vector search may fail until Qdrant is available")
    
    # Initialize MinIO connection
    try:
        from app.core.storage import get_minio_client, ensure_minio_bucket, verify_minio_connection
        client = get_minio_client()
        ensure_minio_bucket()  # Synchronous function
        if verify_minio_connection():  # Synchronous function
            print("[OK] MinIO connection verified")
        else:
            print("[WARN] MinIO connection verification failed")
    except Exception as e:
        print(f"[WARN] Failed to initialize MinIO: {e}")
        print("   File storage may fail until MinIO is available")
    
    yield
    
    # Shutdown
    print("[SHUTDOWN] Suraksh Backend API shutting down...")
    
    # Close Neo4j connection (Phase 2 - optional for Phase 1)
    try:
        from app.core.database import close_neo4j_driver
        await close_neo4j_driver()
        print("[OK] Neo4j connection closed")
    except Exception as e:
        print(f"[WARN] Error closing Neo4j connection: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="Suraksh Intelligence Platform API",
    description="High-security intelligence platform with GraphRAG capabilities",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS Middleware (configure for production)
# #region agent log
import json
try:
    with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
        f.write(json.dumps({"location":"main.py:55","message":"CORS middleware setup","data":{"corsOrigins":settings.CORS_ORIGINS},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + '\n')
except: pass
# #endregion
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    """Root endpoint for health checks."""
    return {
        "service": "Suraksh Backend API",
        "status": "operational",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Detailed health check endpoint."""
    # #region agent log
    import json
    try:
        with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
            f.write(json.dumps({"location":"main.py:75","message":"Health check endpoint called","data":{},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
    except: pass
    # #endregion
    return {
        "status": "healthy",
        "service": "suraksh-backend",
    }


# Fixed: Add base /api/v1/ endpoint to handle frontend health checks
@app.get("/api/v1/", tags=["Health"])
async def api_v1_root() -> dict[str, Any]:
    """
    Base API v1 endpoint for health checks and API discovery.
    
    Returns:
        API version information and available endpoints
    """
    return {
        "api_version": "v1",
        "service": "Suraksh Backend API",
        "status": "operational",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "vault": "/api/v1/vault",
            "ingest": "/api/v1/ingest",
            "search": "/api/v1/search",
            "deepsearch": "/api/v1/deepsearch",
        },
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors with detailed messages."""
    # #region agent log
    import json
    try:
        # Try to read the request body for debugging
        body = None
        try:
            body_bytes = await request.body()
            if body_bytes:
                import json as json_lib
                try:
                    body = json_lib.loads(body_bytes)
                except:
                    body = body_bytes.decode('utf-8', errors='ignore')
        except:
            pass
        
        with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
            f.write(json.dumps({"location":"main.py:validation_exception_handler","message":"Request validation error","data":{"errors":exc.errors(),"body":body,"path":str(request.url.path),"method":request.method},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
    except: pass
    # #endregion
    # Fixed: Return 400 for validation errors (client error) instead of 422
    # Extract first error message for clarity
    error_messages = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "Validation error")
        error_messages.append(f"{field}: {msg}" if field else msg)
    
    # Log to console for immediate debugging
    print(f"[VALIDATION ERROR] Path: {request.url.path}, Errors: {error_messages}")
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation error",
            "detail": error_messages[0] if error_messages else "Invalid request data",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    # #region agent log
    import json
    try:
        with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
            f.write(json.dumps({"location":"main.py:84","message":"Global exception handler","data":{"error":str(exc),"path":str(request.url) if hasattr(request,'url') else None},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
    except: pass
    # #endregion
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# Import API routers
# Fixed: Make graph_rag endpoints optional to allow backend to start without full dependencies
from app.api.v1.endpoints import auth, vault

# Include auth router (required for login)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# Include vault router (required for file operations)
app.include_router(vault.router, prefix="/api/v1/vault", tags=["Vault"])

# Include optional routers (may fail if graph_rag dependencies are missing)
# Fixed: Catch all exceptions, not just ImportError, to ensure router registration
ingest_router_registered = False
search_router_registered = False

# Fixed: Always register ingest router, even if import fails
# This ensures the endpoint exists and returns proper error messages instead of 404
# #region agent log
import json
try:
    with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
        f.write(json.dumps({"location":"main.py:ingest_router_registration","message":"Starting ingest router registration","data":{},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"A,B,C"}) + '\n')
except: pass
# #endregion
try:
    from app.api.v1.endpoints import ingest
    # #region agent log
    try:
        with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
            f.write(json.dumps({"location":"main.py:ingest_router_registration","message":"Ingest module imported successfully","data":{"router_exists":hasattr(ingest,'router'),"router_routes_count":len(ingest.router.routes) if hasattr(ingest,'router') else 0},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + '\n')
    except: pass
    # #endregion
    try:
        app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["Ingest"])
        ingest_router_registered = True
        print("[OK] Ingest router registered successfully")
        # #region agent log
        try:
            with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
                f.write(json.dumps({"location":"main.py:ingest_router_registration","message":"Ingest router registered successfully","data":{"registered":True,"app_routes_count":len([r for r in app.routes if hasattr(r,'path')])},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + '\n')
        except: pass
        # #endregion
    except Exception as e:
        print(f"[WARN] Failed to register ingest router: {e}")
        print("   Ingest endpoints will not be available")
        # #region agent log
        try:
            with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
                f.write(json.dumps({"location":"main.py:ingest_router_registration","message":"Failed to register ingest router","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"B,C"}) + '\n')
        except: pass
        # #endregion
        import traceback
        if settings.DEBUG:
            traceback.print_exc()
except Exception as e:
    print(f"[WARN] Failed to import ingest endpoints: {e}")
    print("   Creating fallback ingest router to prevent 404 errors")
    # #region agent log
    try:
        with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
            f.write(json.dumps({"location":"main.py:ingest_router_registration","message":"Failed to import ingest module","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + '\n')
    except: pass
    # #endregion
    import traceback
    if settings.DEBUG:
        traceback.print_exc()
    
    # Fixed: Create a minimal fallback router so the endpoint exists
    from fastapi import APIRouter, Depends, HTTPException, status
    from app.core.security import get_current_active_user
    from pydantic import BaseModel
    
    fallback_ingest_router = APIRouter()
    
    class IngestFileRequest(BaseModel):
        file_id: str
        extract_graph: bool = True
    
    @fallback_ingest_router.post("/file", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    async def ingest_file_fallback(
        request: IngestFileRequest,
        current_user = Depends(get_current_active_user),
    ):
        """Fallback endpoint when ingest service is unavailable."""
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingest service is not available. GraphRAG dependencies may be missing or misconfigured. Please check backend logs for details."
        )
    
    @fallback_ingest_router.post("/", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    async def ingest_data_fallback(
        current_user = Depends(get_current_active_user),
    ):
        """Fallback endpoint when ingest service is unavailable."""
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingest service is not available. GraphRAG dependencies may be missing or misconfigured. Please check backend logs for details."
        )
    
    app.include_router(fallback_ingest_router, prefix="/api/v1/ingest", tags=["Ingest"])
    ingest_router_registered = True
    print("[OK] Fallback ingest router registered (service unavailable)")

# Register search router
try:
    from app.api.v1.endpoints import search
    try:
        app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
        search_router_registered = True
        print("[OK] Search router registered successfully")
    except Exception as e:
        print(f"[WARN] Failed to register search router: {e}")
        print("   Search endpoints will not be available")
        import traceback
        if settings.DEBUG:
            traceback.print_exc()
except Exception as e:
    print(f"[WARN] Failed to import search endpoints: {e}")
    print("   Search endpoints will not be available")
    import traceback
    if settings.DEBUG:
        traceback.print_exc()

# Register DeepSearch-RAG-Sentinel router
deepsearch_router_registered = False
try:
    from app.api.v1.endpoints import deepsearch
    try:
        app.include_router(deepsearch.router, prefix="/api/v1/deepsearch", tags=["DeepSearch-RAG-Sentinel"])
        deepsearch_router_registered = True
        print("[OK] DeepSearch-RAG-Sentinel router registered successfully")
    except Exception as e:
        print(f"[WARN] Failed to register DeepSearch router: {e}")
        print("   DeepSearch endpoints will not be available")
        import traceback
        if settings.DEBUG:
            traceback.print_exc()
except Exception as e:
    print(f"[WARN] Failed to import DeepSearch endpoints: {e}")
    print("   DeepSearch endpoints will not be available")
    import traceback
    if settings.DEBUG:
        traceback.print_exc()

# Log router registration status
print("[INFO] Router registration status:")
print(f"   - Auth: [OK]")
print(f"   - Vault: [OK]")
print(f"   - Ingest: {'[OK]' if ingest_router_registered else '[FAIL]'}")
print(f"   - Search: {'[OK]' if search_router_registered else '[FAIL]'}")
print(f"   - DeepSearch-RAG-Sentinel: {'[OK]' if deepsearch_router_registered else '[FAIL]'}")

# Fixed: Verify ingest routes are accessible
if ingest_router_registered:
    ingest_routes = [r for r in app.routes if hasattr(r, 'path') and '/ingest' in r.path]
    print(f"[INFO] Ingest routes registered: {len(ingest_routes)}")
    for route in ingest_routes:
        methods = list(route.methods) if hasattr(route, 'methods') and route.methods else []
        print(f"   - {route.path} {methods}")
    # #region agent log
    try:
        with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
            f.write(json.dumps({"location":"main.py:route_verification","message":"Ingest routes verification","data":{"ingest_routes_count":len(ingest_routes),"routes":[{"path":r.path,"methods":list(r.methods) if hasattr(r,'methods') and r.methods else []} for r in ingest_routes]},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"A,B"}) + '\n')
    except: pass
    # #endregion

# Fixed: Add diagnostic endpoint to list all registered routes
@app.get("/api/debug/routes", tags=["Debug"])
async def list_routes() -> dict:
    """List all registered routes for debugging."""
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": getattr(route, "name", "unknown")
            })
    # Filter for ingest routes specifically
    ingest_routes = [r for r in routes if "/ingest" in r["path"]]
    return {
        "total_routes": len(routes),
        "ingest_routes": ingest_routes,
        "all_routes": sorted(routes, key=lambda x: x["path"])
    }


if __name__ == "__main__":
    import uvicorn
    # #region agent log
    try:
        with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
            f.write(json.dumps({"location":"main.py:server_start","message":"Starting uvicorn server","data":{"host":"0.0.0.0","port":8000,"reload":settings.DEBUG},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
    except: pass
    # #endregion
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

