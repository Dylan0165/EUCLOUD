from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
import logging
from urllib.parse import urlparse

from models import get_db, User
from schemas import UserRegister, UserLogin, AuthResponse
from auth import create_access_token, get_current_user, COOKIE_NAME, COOKIE_MAX_AGE

router = APIRouter()
logger = logging.getLogger(__name__)


def normalize_redirect(redirect: str | None) -> str:
    """
    Normalize redirect URL to safe relative path.
    
    Security rules:
    1. Only allow relative paths (starting with /)
    2. No absolute URLs (prevent open redirect vulnerabilities)
    3. Default to /dashboard if invalid or missing
    
    Args:
        redirect: Raw redirect parameter from query string
        
    Returns:
        Safe relative path like /dashboard, /eutype, /cloud
    """
    # Default fallback
    default = "/dashboard"
    
    # If empty or None, return default
    if not redirect or not redirect.strip():
        logger.debug(f"🔀 Redirect empty, using default: {default}")
        return default
    
    redirect = redirect.strip()
    
    # Parse to check for absolute URLs
    parsed = urlparse(redirect)
    
    # If it has a scheme (http://, https://) or netloc (domain), reject it
    if parsed.scheme or parsed.netloc:
        logger.warning(f"🚫 Rejected absolute redirect URL: {redirect}, using default: {default}")
        return default
    
    # Must start with /
    if not redirect.startswith('/'):
        logger.warning(f"🚫 Rejected non-relative redirect: {redirect}, using default: {default}")
        return default
    
    # Normalize path (remove double slashes, resolve ..)
    path = parsed.path or redirect
    
    # Basic path traversal protection
    if '..' in path or '//' in path:
        logger.warning(f"🚫 Rejected unsafe redirect path: {redirect}, using default: {default}")
        return default
    
    logger.debug(f"✓ Normalized redirect: {path}")
    return path


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister, 
    response: Response,
    redirect: str = None,
    db: Session = Depends(get_db)
):
    """
    SSO Registration Endpoint with Redirect Support
    
    Registers new user and automatically logs them in with SSO cookie.
    
    Query Parameters:
        redirect: Optional redirect URL after successful registration (default: /dashboard)
    
    Flow:
    1. Normalize redirect parameter
    2. Validate email is unique
    3. Create user account
    4. Generate JWT token
    5. Set HttpOnly cookie for SSO
    6. Return user info with redirect
    """
    try:
        # Normalize redirect to safe relative path
        redirect_url = normalize_redirect(redirect)
        logger.debug(f"🔀 Redirect URL after registration: {redirect_url}")
        # Normalize email to lowercase
        email_normalized = user_data.email.lower().strip()
        
        logger.info(f"Registration attempt for email: {email_normalized}")
        logger.debug(f"Password length: {len(user_data.password)} characters")
        
        existing_user = db.query(User).filter(User.email == email_normalized).first()
        if existing_user:
            logger.warning(f"Registration failed: Email {email_normalized} already exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        logger.info(f"Creating user object for {email_normalized}")
        user = User(email=email_normalized)
        
        logger.info(f"Setting password for {email_normalized}")
        user.set_password(user_data.password)
        
        try:
            logger.info(f"Adding user to database session")
            db.add(user)
            
            logger.info(f"Committing transaction")
            db.commit()
            
            logger.info(f"Refreshing user object")
            db.refresh(user)
            
            logger.info(f"User {user_data.email} registered successfully with ID: {user.user_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Database error during registration for {user_data.email}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        
        logger.info(f"Creating access token for user {user.user_id}")
        access_token = create_access_token(user.user_id)
        
        # � Delete any old cookie first
        response.delete_cookie(
            key=COOKIE_NAME,
            path="/",
            domain="192.168.124.50"
        )
        
        # �🔐 SET SSO COOKIE (auto-login after registration)
        response.set_cookie(
            key=COOKIE_NAME,
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            path="/",
            max_age=COOKIE_MAX_AGE,
            domain="192.168.124.50"
        )
        
        logger.info(f"✅ User {user_data.email} registered and logged in - SSO cookie set")
        
        return {
            "success": True,
            "redirect": redirect_url,
            "user": user.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login")
async def login(
    credentials: UserLogin, 
    response: Response,
    request: Request,
    redirect: str = None,
    db: Session = Depends(get_db)
):
    """
    SSO Login Endpoint with Redirect Support
    
    Authenticates user and sets HttpOnly cookie for SSO across all EUsuite apps.
    
    Query Parameters:
        redirect: Optional redirect URL after successful login (default: /dashboard)
    
    Flow:
    1. Extract redirect parameter (default: /dashboard)
    2. Delete old cookie
    3. Validate credentials
    4. Generate JWT token
    5. Set HttpOnly cookie with token
    6. Return JSON response with redirect URL
    
    The cookie is automatically sent with all subsequent requests (credentials: "include")
    """
    try:
        # Normalize redirect to safe relative path
        redirect_url = normalize_redirect(redirect)
        logger.debug(f"🔀 Redirect URL after login: {redirect_url}")
        
        # 🔥 CRITICAL: Delete old cookie IMMEDIATELY - don't validate it!
        response.delete_cookie(
            key=COOKIE_NAME,
            path="/",
            domain="192.168.124.50"
        )
        logger.debug("🗑️ Old SSO cookie deleted at start of login")
        
        # Get identifier (username or email)
        try:
            identifier = credentials.get_identifier()
        except ValueError as e:
            logger.warning(f"Login validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        logger.info(f"🔐 Login attempt for: {identifier}")
        
        # Find user by email (case-insensitive)
        # In our system, username = email
        user = db.query(User).filter(
            User.email.ilike(identifier)  # Case-insensitive search
        ).first()
        
        if not user:
            logger.warning(f"❌ Login failed: User '{identifier}' not found in database")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        logger.info(f"✓ User found: {user.email} (ID: {user.user_id})")
        
        # Verify password
        logger.debug(f"Checking password for user {user.email}")
        password_valid = user.check_password(credentials.password)
        
        if not password_valid:
            logger.warning(f"❌ Login failed: Invalid password for user '{user.email}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        logger.info(f"✓ Password verified for user {user.email}")
        
        # Generate JWT token
        access_token = create_access_token(user.user_id)
        logger.debug(f"✓ JWT token generated for user {user.user_id}")
        
        # � SET NEW SSO COOKIE
        response.set_cookie(
            key=COOKIE_NAME,
            value=access_token,
            httponly=True,           # XSS protection - JavaScript cannot access
            secure=False,            # LAN-only (set True for HTTPS in production)
            samesite="lax",          # CSRF protection - allows navigation
            path="/",                # Cookie available for all paths
            max_age=COOKIE_MAX_AGE,  # 24 hours
            domain="192.168.124.50"  # Shared across all EUsuite apps on this domain
        )
        
        logger.info(f"✅ User {user.email} logged in successfully - SSO cookie set")
        
        # Return JSON response with redirect - session is based on COOKIE, not this response
        return {
            "success": True,
            "redirect": redirect_url,
            "user": {
                "user_id": user.user_id,
                "username": user.email,
                "email": user.email
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout")
async def logout(response: Response):
    """
    SSO Logout Endpoint
    
    Removes the SSO cookie, effectively logging out the user from ALL EUsuite apps.
    
    Flow:
    1. Delete the SSO cookie (no authentication required)
    2. Return success message
    
    After logout, all apps will receive 401 and redirect to login portal.
    Note: We don't validate who is logging out - just delete the cookie.
    """
    logger.info(f"Logout request received")
    
    # 🔓 DELETE SSO COOKIE
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        domain="192.168.124.50"
    )
    
    logger.info(f"✅ SSO cookie deleted - user logged out")
    
    return {"message": "Logged out"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    SSO Authentication Check Endpoint
    
    This is the heart of the SSO system. ALL EUsuite apps call this endpoint
    to verify if the user is logged in.
    
    Flow:
    1. Browser sends request with HttpOnly cookie (automatic with credentials: "include")
    2. get_current_user dependency validates JWT from cookie
    3. If valid → return user info (200)
    4. If invalid/missing → 401 (apps redirect to login portal)
    
    Used by: EuCloud, EuType, EuSheets, EuPhotos, etc.
    """
    logger.debug(f"SSO check for user {current_user.email}")
    return {"user": current_user.to_dict()}


@router.get("/validate")
async def validate_token(request: Request, db: Session = Depends(get_db)):
    """
    SSO Token Validation Endpoint
    
    Validates the JWT token from cookie and returns user info if valid.
    Returns 401 if token is invalid, expired, or missing.
    
    This is used by all EUsuite apps to check if user is logged in.
    
    Returns:
        - User info if token is valid
        - 401 Unauthorized if token is invalid, expired, or missing
    """
    try:
        # Try to get token from cookie
        token = request.cookies.get(COOKIE_NAME)
        
        if not token:
            logger.debug("Validate: No token in cookie")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authentication token provided"
            )
        
        # Try to decode and validate token
        from jose import JWTError, jwt
        from auth import SECRET_KEY, ALGORITHM
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("user_id")
            
            if user_id is None:
                logger.debug("Validate: Token missing user_id")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user from database
            user = db.query(User).filter(User.user_id == user_id).first()
            
            if user is None:
                logger.debug(f"Validate: User {user_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            logger.debug(f"Validate: Token valid for user {user.email}")
            return {
                "user_id": user.user_id,
                "username": user.email,
                "email": user.email
            }
            
        except JWTError as e:
            logger.debug(f"Validate: JWT error - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validate: Unexpected error - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validation failed"
        )


@router.get("/test-cookie")
async def test_cookie(request: Request):
    """
    Test endpoint to check if SSO cookie is present and readable
    
    Useful for debugging SSO issues.
    """
    cookie_value = request.cookies.get(COOKIE_NAME)
    
    if cookie_value:
        logger.info(f"✅ SSO cookie found: {COOKIE_NAME}")
        return {
            "cookie_present": True,
            "cookie_name": COOKIE_NAME,
            "cookie_value_length": len(cookie_value),
            "message": "SSO cookie is present and readable"
        }
    else:
        logger.warning(f"❌ SSO cookie not found: {COOKIE_NAME}")
        return {
            "cookie_present": False,
            "cookie_name": COOKIE_NAME,
            "message": "SSO cookie is NOT present",
            "all_cookies": list(request.cookies.keys())
        }


@router.get("/debug/users")
async def debug_users(db: Session = Depends(get_db)):
    """
    DEBUG ONLY: List all users in database
    ⚠️ REMOVE IN PRODUCTION
    """
    users = db.query(User).all()
    return {
        "total_users": len(users),
        "users": [
            {
                "user_id": u.user_id,
                "email": u.email,
                "has_password": bool(u.password_hash),
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ]
    }
