# 🔧 Backend SSO Implementation Guide

**Status:** ⏳ PENDING - Frontend is compleet, backend moet nog geïmplementeerd worden

Deze guide helpt je de backend aan te passen voor SSO cookie-based authentication.

---

## 🎯 Wat Moet de Backend Doen?

1. **Cookie-based sessies** ipv JWT tokens
2. **`/api/auth/me` endpoint** voor SSO check
3. **CORS configuratie** voor credentials
4. **Middleware** voor cookie verificatie op alle protected routes

---

## 📝 Step-by-Step Implementation

### Step 1: Install Dependencies

```bash
pip install flask-session redis
```

### Step 2: Configure Session Management

**File:** `backend/config.py`

```python
import os
from datetime import timedelta

class Config:
    # Session settings
    SESSION_TYPE = 'redis'  # Of 'filesystem' voor development
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Cookie settings
    SESSION_COOKIE_NAME = 'session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # True in productie (HTTPS)
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_DOMAIN = '192.168.124.50'  # Shared tussen alle apps
    SESSION_COOKIE_PATH = '/'
    
    # Secret key voor session signing
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Redis (als je SESSION_TYPE = 'redis' gebruikt)
    SESSION_REDIS = redis.from_url(
        os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    )
```

### Step 3: Initialize Session

**File:** `backend/app.py` of `backend/main.py`

```python
from flask import Flask
from flask_session import Session
from flask_cors import CORS
import redis

app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize session
Session(app)

# Configure CORS with credentials
CORS(app, 
     origins=[
         "http://192.168.124.50:30090",  # Login Portal
         "http://192.168.124.50:30500",  # EuCloud
         "http://192.168.124.50:30600",  # EuType
         "http://192.168.124.50:30700"   # EuSheets
     ],
     supports_credentials=True,
     allow_headers=["Content-Type"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
```

### Step 4: Create Auth Middleware

**File:** `backend/auth.py`

```python
from functools import wraps
from flask import session, jsonify, request

def login_required(f):
    """Decorator voor protected routes - checkt session cookie"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user_id exists in session
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Add user to request context
        request.current_user_id = session['user_id']
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Helper om current user op te halen"""
    from models import User
    
    if 'user_id' not in session:
        return None
    
    return User.query.get(session['user_id'])
```

### Step 5: Implement `/auth/me` Endpoint

**File:** `backend/routes/auth.py`

```python
from flask import Blueprint, jsonify, session
from auth import get_current_user
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/me', methods=['GET'])
def get_me():
    """
    SSO check endpoint
    Returns current user if valid session exists
    """
    user = get_current_user()
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify({
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }), 200
```

### Step 6: Update Protected Routes

**Before (JWT token):**
```python
from flask_jwt_extended import jwt_required, get_jwt_identity

@app.route('/files/upload', methods=['POST'])
@jwt_required()
def upload_file():
    user_id = get_jwt_identity()
    # ... rest of code
```

**After (Session cookie):**
```python
from auth import login_required, get_current_user

@app.route('/files/upload', methods=['POST'])
@login_required
def upload_file():
    user = get_current_user()
    # ... rest of code
```

### Step 7: Remove JWT Extensions

**Remove from requirements.txt:**
```
flask-jwt-extended  # ❌ Remove this
```

**Remove from app initialization:**
```python
# ❌ Remove these
from flask_jwt_extended import JWTManager
jwt = JWTManager(app)
```

---

## 🔐 Session Login (FROM LOGIN PORTAL)

De Login Portal zal na succesvolle login een session cookie zetten:

```python
from flask import session

@app.route('/login', methods=['POST'])
def login():
    # Verify credentials
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Set session
    session['user_id'] = user.id
    session.permanent = True  # Use PERMANENT_SESSION_LIFETIME
    
    return jsonify({
        "user": {
            "id": user.id,
            "email": user.email
        }
    }), 200
```

**BELANGRIJK:** Deze login logic komt in de **Login Portal**, niet in EuCloud!

---

## 🧪 Testing

### 1. Test Session Creation
```bash
# Login via Login Portal
curl -X POST http://192.168.124.50:30090/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  --cookie-jar cookies.txt \
  --verbose
```

Check response headers voor `Set-Cookie`:
```
Set-Cookie: session=abc123...; HttpOnly; SameSite=Lax; Path=/; Domain=192.168.124.50
```

### 2. Test SSO Check
```bash
# Use cookie from step 1
curl -X GET http://192.168.124.50:30500/api/auth/me \
  --cookie cookies.txt \
  --verbose
```

Expected response:
```json
{
  "user": {
    "id": 1,
    "email": "test@example.com"
  }
}
```

### 3. Test Protected Endpoint
```bash
curl -X GET http://192.168.124.50:30500/api/files/list \
  --cookie cookies.txt
```

Should return files, not 401.

---

## 🔄 Migration Strategy

### Phase 1: Add Session Support (Keep JWT)
1. Add session configuration
2. Add `/auth/me` endpoint
3. Test SSO check works
4. Keep JWT for backwards compatibility

### Phase 2: Update Routes
1. Add session checks to all protected routes
2. Test with session cookie
3. Keep JWT fallback

### Phase 3: Remove JWT
1. Remove `@jwt_required` decorators
2. Remove JWT configuration
3. Remove JWT dependencies
4. Deploy

---

## 📊 Checklist

### Configuration
- [ ] Flask-Session installed
- [ ] Redis configured (or filesystem sessions)
- [ ] Session cookie settings correct
- [ ] CORS allows credentials
- [ ] Secret key set

### Endpoints
- [ ] `/auth/me` endpoint created
- [ ] Returns 200 with user for valid session
- [ ] Returns 401 for invalid/missing session

### Middleware
- [ ] `@login_required` decorator created
- [ ] Works with session cookie
- [ ] All protected routes use it

### Testing
- [ ] Session cookie is set after login
- [ ] Cookie has correct HttpOnly/SameSite settings
- [ ] `/auth/me` works with cookie
- [ ] Protected routes work with cookie
- [ ] CORS headers correct

---

## 🚨 Common Pitfalls

### 1. Cookie Domain Mismatch
```python
# ❌ Wrong
SESSION_COOKIE_DOMAIN = 'localhost'  # Won't work for 192.168.124.50

# ✅ Correct
SESSION_COOKIE_DOMAIN = '192.168.124.50'
```

### 2. CORS Not Allowing Credentials
```python
# ❌ Wrong
CORS(app)

# ✅ Correct
CORS(app, supports_credentials=True, origins=[...])
```

### 3. Session Not Persisting
```python
# ❌ Wrong
app.config['SESSION_TYPE'] = None  # In-memory only

# ✅ Correct
app.config['SESSION_TYPE'] = 'redis'  # Persists across restarts
```

---

## 📚 Documentation

- [Flask-Session Docs](https://flask-session.readthedocs.io/)
- [Flask CORS Docs](https://flask-cors.readthedocs.io/)
- [Redis Session Store](https://redis.io/docs/manual/patterns/session/)

---

## ✅ Success Criteria

Backend implementation is complete when:

1. ✅ User can login via Login Portal
2. ✅ Session cookie is set with correct settings
3. ✅ `/auth/me` returns user for valid cookie
4. ✅ All protected routes work with cookie
5. ✅ No JWT dependencies remain
6. ✅ CORS works with credentials
7. ✅ Tests pass

---

**Next Step:** Start with Step 1 and work through each step sequentially.
