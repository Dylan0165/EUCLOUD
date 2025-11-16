from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from models import get_db, User
from schemas import UserRegister, UserLogin, AuthResponse
from auth import create_access_token, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
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
        
        logger.info(f"Converting user to dict")
        user_dict = user.to_dict()
        
        logger.info(f"Registration successful, returning response")
        return {
            "message": "User registered successfully",
            "access_token": access_token,
            "user": user_dict
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
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    try:
        logger.info(f"Login attempt for email: {credentials.email}")
        
        user = db.query(User).filter(User.email == credentials.email).first()
        
        if not user:
            logger.warning(f"Login failed: User {credentials.email} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.check_password(credentials.password):
            logger.warning(f"Login failed: Invalid password for {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(user.user_id)
        logger.info(f"User {credentials.email} logged in successfully")
        
        return {
            "message": "Login successful",
            "access_token": access_token,
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
async def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logout successful"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"user": current_user.to_dict()}
