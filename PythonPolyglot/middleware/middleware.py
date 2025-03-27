from fastapi import Request, HTTPException
import logging

logger = logging.getLogger(__name__)

# Routes that should NOT require authentication
EXCLUDED_ROUTES = ["/transactions", "/create_transaction", "/get_user"]

async def auth_middleware(request: Request, call_next):
    # Check if request path starts with an excluded route
    if any(request.url.path.startswith(route) for route in EXCLUDED_ROUTES):
        return await call_next(request)  # Skip authentication

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    # Token validation logic (placeholder)
    token = auth_header.split("Bearer ")[1]
    if token != "VALID_TOKEN":
        raise HTTPException(status_code=401, detail="Invalid token")

    response = await call_next(request)
    return response
