from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
import logging

from models import get_db, User
from schemas import UserRegister, UserLogin, AuthResponse
from auth import create_access_token, get_current_user, COOKIE_NAME, COOKIE_MAX_AGE

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister, 
    response: Response,
    db: Session = Depends(get_db)
):
    """
    SSO Registration Endpoint
    
    Registers new user and automatically logs them in with SSO cookie.
    
    Flow:
    1. Validate email is unique
    2. Create user account
    3. Generate JWT token
    4. Set HttpOnly cookie for SSO
    5. Return user info
    """
    try:
        logger.info(f"Registration attempt for email: {user_data.email}")
        logger.debug(f"Password length: {len(user_data.password)} characters")
        
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning(f"Registration failed: Email {user_data.email} already exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        logger.info(f"Creating user object for {user_data.email}")
        user = User(email=user_data.email)
        
        logger.info(f"Setting password for {user_data.email}")
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
        
        # 🔐 SET SSO COOKIE (auto-login after registration)
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
            "message": "User registered successfully",
            "access_token": access_token,
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
    db: Session = Depends(get_db)
):
    """
    SSO Login Endpoint
    
    Authenticates user and sets HttpOnly cookie for SSO across all EUsuite apps.
    
    Flow:
    1. Validate credentials
    2. Generate JWT token
    3. Set HttpOnly cookie with token
    4. Return JSON response (for compatibility)
    
    The cookie is automatically sent with all subsequent requests (credentials: "include")
    """
    try:
        # Accept both username and email as login identifier
        identifier = credentials.identifier
        if not identifier:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Either username or email must be provided"
            )
        
        logger.info(f"Login attempt for: {identifier}")
        
        # Try to find user by email (username and email are the same in our system)
        user = db.query(User).filter(User.email == identifier).first()
        
        if not user:
            logger.warning(f"Login failed: User {identifier} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.check_password(credentials.password):
            logger.warning(f"Login failed: Invalid password for {identifier}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate JWT token
        access_token = create_access_token(user.user_id)
        
        # 🔐 SET SSO COOKIE
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
        
        # Return JSON response (for compatibility, but cookie is what matters)
        return {
            "message": "Login successful",
            "access_token": access_token,  # Still returned for backwards compatibility
            "user": user.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    SSO Logout Endpoint
    
    Removes the SSO cookie, effectively logging out the user from ALL EUsuite apps.
    
    Flow:
    1. Verify user is authenticated (get_current_user)
    2. Delete the SSO cookie
    3. Return success message
    
    After logout, all apps will receive 401 and redirect to login portal.
    """
    logger.info(f"User {current_user.email} logging out")
    
    # 🔓 DELETE SSO COOKIE
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        domain="192.168.124.50"
    )
    
    logger.info(f"✅ User {current_user.email} logged out - SSO cookie deleted")
    
    return {"message": "Logout successful"}


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
