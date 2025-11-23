# EUCloud SSO Authenticatie Flow

## Overzicht

De EUCloud frontend gebruikt nu een volledig cookie-based SSO systeem dat identiek is aan het EUsuite Dashboard.

## Architectuur

```
┌─────────────────────────────────────────────────────────────────┐
│                     EUsuite SSO Systeem                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │  EUCloud     │    │  Login       │    │  Auth        │    │
│  │  Frontend    │───▶│  Portal      │───▶│  Backend     │    │
│  │  :30080      │    │  :30090      │    │  :30500      │    │
│  └──────────────┘    └──────────────┘    └──────────────┘    │
│         ▲                                        │             │
│         │                                        │             │
│         └────────────────────────────────────────┘             │
│                   eusuite_token cookie                         │
│              Domain=192.168.124.50                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Frontend: `useAuth` Hook

### **Bestand:** `frontend/src/context/AuthContext.jsx`

```javascript
export const useAuth = () => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Bij mount: valideer SSO session
  useEffect(() => {
    validateSession()
  }, [])

  const validateSession = async () => {
    const response = await fetch(
      'http://192.168.124.50:30500/api/auth/validate',
      { credentials: 'include' }
    )
    
    if (response.status === 401) {
      // Redirect naar login portal
      window.location.href = 'http://192.168.124.50:30090/login?redirect=/eucloud'
      return
    }
    
    if (response.status === 200) {
      const data = await response.json()
      if (data.valid && data.user) {
        setUser(data.user)
      }
    }
    
    setLoading(false)
  }

  const logout = async () => {
    await fetch('http://192.168.124.50:30500/api/auth/logout', {
      method: 'POST',
      credentials: 'include'
    })
    
    window.location.href = 'http://192.168.124.50:30090/login?redirect=/eucloud'
  }
}
```

### **Key Features:**

✅ **Bij mount:** `GET /api/auth/validate` met `credentials: "include"`  
✅ **Bij 401:** Redirect naar login portal met `/eucloud` redirect  
✅ **Bij 200 + valid:** User state vullen  
✅ **Bij catch:** Alleen error loggen, GEEN redirect  
✅ **Logout:** Cookie verwijderen + redirect naar login  

## App Component

### **Bestand:** `frontend/src/App.jsx`

```javascript
function AppContent() {
  const { user, loading } = useAuth()
  
  if (loading) {
    return <LoadingScreen />
  }
  
  if (!user) {
    return <div>Redirecting to login portal...</div>
  }
  
  // User authenticated - render app
  return <Router>...</Router>
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
```

### **Key Features:**

✅ **Loading state:** Tonen tijdens SSO validatie  
✅ **Geen user:** App NIET renderen (redirect al uitgevoerd)  
✅ **User aanwezig:** Volledige app renderen  

## API Interceptor

### **Bestand:** `frontend/src/services/api.js`

```javascript
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = 'http://192.168.124.50:30090/login?redirect=/eucloud'
    }
    return Promise.reject(error)
  }
)
```

### **Key Features:**

✅ **Axios interceptor:** Vangt alle 401 responses op  
✅ **Automatic redirect:** Naar login portal bij session expiry  

## Backend: Validate Endpoint

### **Bestand:** `backend/routes/auth.py`

```python
@router.get("/validate")
async def validate_token(request: Request, db: Session = Depends(get_db)):
    """
    Validates JWT token from cookie.
    Returns 401 if invalid, expired, or missing.
    """
    token = request.cookies.get(COOKIE_NAME)
    
    if not token:
        raise HTTPException(status_code=401, detail="No token")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "valid": True,
            "user": {
                "user_id": user.user_id,
                "username": user.email,
                "email": user.email
            }
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### **Response Format:**

```json
{
  "valid": true,
  "user": {
    "user_id": 123,
    "username": "user@example.com",
    "email": "user@example.com"
  }
}
```

## Flow Diagram

### **Scenario 1: Nieuwe gebruiker (niet ingelogd)**

```
1. User bezoekt http://192.168.124.50:30080/dashboard
   ↓
2. useAuth() mount → GET /api/auth/validate (geen cookie)
   ↓
3. Backend: 401 Unauthorized
   ↓
4. Frontend: window.location.href = login portal + ?redirect=/eucloud
   ↓
5. User logt in op login portal
   ↓
6. Backend: Set eusuite_token cookie (Domain=192.168.124.50)
   ↓
7. Login portal: redirect naar http://192.168.124.50:30080/eucloud
   ↓
8. useAuth() mount → GET /api/auth/validate (cookie present!)
   ↓
9. Backend: 200 OK + { valid: true, user: {...} }
   ↓
10. Frontend: setUser(data.user) → app renders
```

### **Scenario 2: Bestaande sessie**

```
1. User bezoekt http://192.168.124.50:30080/dashboard
   ↓
2. useAuth() mount → GET /api/auth/validate (cookie present)
   ↓
3. Backend: 200 OK + { valid: true, user: {...} }
   ↓
4. Frontend: setUser(data.user) → app renders (geen redirect!)
```

### **Scenario 3: Logout**

```
1. User klikt "Logout" in EUCloud
   ↓
2. Frontend: await fetch('/api/auth/logout', { POST })
   ↓
3. Backend: Delete cookie (Domain=192.168.124.50, Path=/)
   ↓
4. Frontend: window.location.href = login portal
   ↓
5. Cookie deleted = uitgelogd in ALLE EUsuite apps
```

### **Scenario 4: Session expiry tijdens gebruik**

```
1. User is actief in EUCloud, JWT token expired
   ↓
2. Frontend maakt API call → axios GET /api/files
   ↓
3. Backend: 401 Unauthorized (token expired)
   ↓
4. Axios interceptor: detecteert 401
   ↓
5. Frontend: window.location.href = login portal + ?redirect=/eucloud
   ↓
6. User logt opnieuw in → nieuwe cookie → redirect terug
```

## Security Features

### **Cookie Settings**

```javascript
// Backend sets cookie
response.set_cookie(
    key="eusuite_token",
    value=jwt_token,
    httponly=True,        // JavaScript kan niet bij cookie
    secure=False,         // True voor HTTPS in productie
    samesite="lax",       // CSRF bescherming
    path="/",             // Cookie voor alle paths
    domain="192.168.124.50"  // Shared across alle ports
)
```

### **Bescherming tegen:**

✅ **XSS:** `httponly=True` voorkomt JavaScript toegang  
✅ **CSRF:** `samesite="lax"` blokkeert cross-site requests  
✅ **Open Redirect:** Backend normaliseert redirect paths  
✅ **Path Traversal:** `..` en `//` geblokkeerd  
✅ **Session Fixation:** Oude cookie wordt verwijderd bij login  

## Testing Checklist

### **Na deployment:**

1. **Clear alle cookies:**
   - DevTools → Application → Cookies → Delete all

2. **Test nieuwe login:**
   - Ga naar `http://192.168.124.50:30080`
   - Verwacht: Redirect naar login portal
   - Login met credentials
   - Verwacht: Redirect terug naar EUCloud dashboard
   - Check DevTools → Cookies → Moet **1 cookie** zijn met `Domain: 192.168.124.50`

3. **Test bestaande sessie:**
   - Refresh page
   - Verwacht: Direct dashboard (geen redirect)

4. **Test logout:**
   - Klik logout button
   - Verwacht: Cookie verwijderd + redirect naar login portal

5. **Test cross-app SSO:**
   - Login in EUCloud (:30080)
   - Open EuType (:30081)
   - Verwacht: Direct ingelogd (dezelfde cookie!)

6. **Test session expiry:**
   - Wacht 24 uur (JWT expiry)
   - Maak API call
   - Verwacht: Redirect naar login portal

## Belangrijke URLs

| Component | URL | Doel |
|-----------|-----|------|
| EUCloud Frontend | `http://192.168.124.50:30080` | Hoofdapplicatie |
| Login Portal | `http://192.168.124.50:30090/login` | SSO login |
| Auth Backend | `http://192.168.124.50:30500` | API endpoints |
| Validate Endpoint | `http://192.168.124.50:30500/api/auth/validate` | Session check |
| Logout Endpoint | `http://192.168.124.50:30500/api/auth/logout` | Cookie delete |

## Removed Features

❌ **localStorage** - Niet meer gebruikt voor tokens  
❌ **sessionStorage** - Niet meer gebruikt  
❌ **axios defaults.headers** - Niet meer nodig (cookies automatisch)  
❌ **JWT in Authorization header** - Alleen cookies  
❌ **Frontend login forms** - Centraal login portal  
❌ **SSO_CONFIG helper functions** - Direct fetch calls  

## Migration Complete

De EUCloud frontend is nu volledig geconverteerd naar het centralized SSO systeem met cookie-based authenticatie. Alle oude auth code is verwijderd en vervangen door de `useAuth` hook die identiek werkt aan het EUsuite Dashboard.
