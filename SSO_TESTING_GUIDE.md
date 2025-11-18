# 🧪 SSO Cookie Integration Testing Guide

**Complete end-to-end testing for EUsuite SSO implementation**

---

## 🎯 Test Scenarios

### ✅ Scenario 1: Fresh Login Flow

**Steps:**
1. User has no cookie
2. User visits EuCloud
3. Redirected to Login Portal
4. User logs in
5. Cookie is set
6. Redirected back to EuCloud
7. Dashboard loads

**Expected:**
- Cookie `eusuite_token` is set
- All apps can access cookie
- `/auth/me` returns user info

---

### ✅ Scenario 2: Multi-App Access

**Steps:**
1. User logged into EuCloud (has cookie)
2. User opens EuType in new tab
3. EuType checks `/auth/me`
4. Dashboard loads immediately (no login)

**Expected:**
- Same cookie works for both apps
- No additional login required
- User info consistent across apps

---

### ✅ Scenario 3: Logout Flow

**Steps:**
1. User logged into multiple apps
2. User clicks logout in EuCloud
3. Cookie is deleted
4. All apps receive 401 on next request
5. All apps redirect to Login Portal

**Expected:**
- Cookie deleted
- All apps logged out simultaneously
- Clean redirect to login

---

## 🔧 Backend Tests

### Test 1: Login Sets Cookie

```bash
# Execute login
curl -X POST http://192.168.124.50:30500/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword"
  }' \
  --cookie-jar cookies.txt \
  --verbose

# Check for Set-Cookie header
# Expected output:
# Set-Cookie: eusuite_token=eyJhbGc...; HttpOnly; SameSite=Lax; Path=/; Domain=192.168.124.50; Max-Age=86400
```

**Verify:**
- [ ] Response contains `Set-Cookie` header
- [ ] Cookie name is `eusuite_token`
- [ ] HttpOnly flag present
- [ ] SameSite=Lax
- [ ] Domain=192.168.124.50
- [ ] Max-Age=86400

---

### Test 2: Auth Check with Cookie

```bash
# Check authentication
curl -X GET http://192.168.124.50:30500/api/auth/me \
  --cookie cookies.txt \
  --verbose

# Expected output:
# {
#   "user": {
#     "user_id": 1,
#     "email": "test@example.com",
#     "created_at": "2025-11-18T..."
#   }
# }
```

**Verify:**
- [ ] Status code 200
- [ ] User object returned
- [ ] Email matches login

---

### Test 3: Auth Check WITHOUT Cookie

```bash
# Try without cookie
curl -X GET http://192.168.124.50:30500/api/auth/me \
  --verbose

# Expected output:
# Status: 401 Unauthorized
# {
#   "detail": "Could not validate credentials"
# }
```

**Verify:**
- [ ] Status code 401
- [ ] Error message returned
- [ ] No user data

---

### Test 4: Cookie Debug Endpoint

```bash
# With cookie
curl -X GET http://192.168.124.50:30500/api/auth/test-cookie \
  --cookie cookies.txt

# Expected output:
# {
#   "cookie_present": true,
#   "cookie_name": "eusuite_token",
#   "cookie_value_length": 215,
#   "message": "SSO cookie is present and readable"
# }
```

**Verify:**
- [ ] cookie_present = true
- [ ] Cookie value length > 0

```bash
# Without cookie
curl -X GET http://192.168.124.50:30500/api/auth/test-cookie

# Expected output:
# {
#   "cookie_present": false,
#   "cookie_name": "eusuite_token",
#   "message": "SSO cookie is NOT present",
#   "all_cookies": []
# }
```

**Verify:**
- [ ] cookie_present = false
- [ ] Helpful error message

---

### Test 5: Protected Endpoint with Cookie

```bash
# List files with cookie
curl -X GET http://192.168.124.50:30500/api/files/list \
  --cookie cookies.txt

# Expected: List of files (or empty array)
```

**Verify:**
- [ ] Status code 200
- [ ] Files array returned (may be empty)
- [ ] No 401 error

---

### Test 6: Logout Deletes Cookie

```bash
# Logout
curl -X POST http://192.168.124.50:30500/api/auth/logout \
  --cookie cookies.txt \
  --cookie-jar cookies.txt \
  --verbose

# Expected:
# Set-Cookie: eusuite_token=; Path=/; Domain=192.168.124.50; Max-Age=0
```

**Verify:**
- [ ] Response contains Set-Cookie with Max-Age=0
- [ ] Cookie removed from cookies.txt
- [ ] Status code 200

```bash
# Try to use deleted cookie
curl -X GET http://192.168.124.50:30500/api/auth/me \
  --cookie cookies.txt

# Expected: 401 Unauthorized
```

**Verify:**
- [ ] Status code 401
- [ ] No user data returned

---

### Test 7: Register Sets Cookie

```bash
# Register new user
curl -X POST http://192.168.124.50:30500/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "newpassword"
  }' \
  --cookie-jar cookies-new.txt \
  --verbose

# Expected:
# Set-Cookie: eusuite_token=...
# Status: 201 Created
```

**Verify:**
- [ ] Status code 201
- [ ] Set-Cookie header present
- [ ] User object returned
- [ ] Access token returned

---

### Test 8: CORS Headers

```bash
# Preflight request (OPTIONS)
curl -X OPTIONS http://192.168.124.50:30500/api/auth/me \
  -H "Origin: http://192.168.124.50:30090" \
  -H "Access-Control-Request-Method: GET" \
  --verbose

# Expected headers:
# Access-Control-Allow-Origin: http://192.168.124.50:30090
# Access-Control-Allow-Credentials: true
# Access-Control-Allow-Methods: ...
```

**Verify:**
- [ ] Access-Control-Allow-Origin matches origin
- [ ] Access-Control-Allow-Credentials: true
- [ ] Access-Control-Allow-Methods includes GET/POST/etc

---

## 🌐 Frontend Tests

### Test 9: Browser Cookie Set

**Manual Test:**
1. Open Browser DevTools
2. Go to Application → Cookies
3. Login via Login Portal
4. Check cookies for `192.168.124.50`

**Verify:**
- [ ] Cookie `eusuite_token` exists
- [ ] HttpOnly flag ✓
- [ ] Secure flag (if HTTPS) ✓
- [ ] SameSite = Lax
- [ ] Domain = 192.168.124.50
- [ ] Path = /
- [ ] Expires = ~24 hours from now

---

### Test 10: Automatic Cookie Send

**Manual Test:**
1. Login to EuCloud
2. Open DevTools → Network
3. Make any API request
4. Check request headers

**Verify:**
- [ ] Request contains `Cookie: eusuite_token=...`
- [ ] No Authorization header (unless backwards compat)
- [ ] Cookie sent automatically

---

### Test 11: Cookie Shared Across Apps

**Manual Test:**
1. Login to EuCloud (port 30500)
2. Open EuType (port 30600) in new tab
3. Check if logged in automatically

**Verify:**
- [ ] EuType loads dashboard immediately
- [ ] No login screen shown
- [ ] Same user info displayed
- [ ] Same cookie in both tabs

---

### Test 12: Logout Affects All Apps

**Manual Test:**
1. Open EuCloud (logged in)
2. Open EuType (logged in)
3. Logout from EuCloud
4. Refresh EuType

**Verify:**
- [ ] Cookie deleted in DevTools
- [ ] EuType redirects to Login Portal
- [ ] Both apps show login screen

---

## 🔒 Security Tests

### Test 13: XSS Protection (HttpOnly)

**Manual Test:**
```javascript
// In browser console
document.cookie
// Should NOT see eusuite_token

// Try to read cookie
document.cookie.includes('eusuite_token')
// Should return false
```

**Verify:**
- [ ] Cookie not accessible via JavaScript
- [ ] document.cookie doesn't show eusuite_token

---

### Test 14: CSRF Protection (SameSite)

**Test:**
Create malicious page on different origin:
```html
<!-- evil.com/attack.html -->
<img src="http://192.168.124.50:30500/api/auth/logout">
```

**Verify:**
- [ ] Cookie NOT sent with request
- [ ] SameSite=Lax blocks cross-site requests
- [ ] User remains logged in

---

### Test 15: Token Expiry

**Test:**
1. Login and get cookie
2. Wait 24+ hours OR manually expire token
3. Try to access protected endpoint

**Verify:**
- [ ] Status code 401
- [ ] Token validation fails
- [ ] User redirected to login

---

## 📊 Integration Test Matrix

| Scenario | Expected Result | Status |
|----------|----------------|--------|
| Login sets cookie | ✅ Cookie in response | ⬜ |
| Cookie auth works | ✅ 200 from /me | ⬜ |
| No cookie = 401 | ❌ 401 from /me | ⬜ |
| Logout deletes cookie | ❌ Cookie removed | ⬜ |
| Cookie shared across apps | ✅ Multi-app access | ⬜ |
| CORS allows credentials | ✅ Headers present | ⬜ |
| HttpOnly blocks JS | ❌ No document.cookie | ⬜ |
| SameSite blocks CSRF | ❌ Cross-site blocked | ⬜ |
| Token expiry works | ❌ 401 after expiry | ⬜ |
| Protected endpoints work | ✅ Files/folders/etc | ⬜ |

---

## 🚀 Automated Test Script

```bash
#!/bin/bash

echo "🧪 Starting SSO Cookie Integration Tests"
echo "=========================================="

BASE_URL="http://192.168.124.50:30500"
EMAIL="test@example.com"
PASSWORD="testpassword"

# Test 1: Login
echo "Test 1: Login sets cookie..."
RESPONSE=$(curl -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  --cookie-jar cookies.txt \
  -w "\n%{http_code}" \
  -s)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Test 1 PASSED"
else
  echo "❌ Test 1 FAILED (HTTP $HTTP_CODE)"
fi

# Test 2: Auth check with cookie
echo "Test 2: Auth check with cookie..."
HTTP_CODE=$(curl -X GET "$BASE_URL/api/auth/me" \
  --cookie cookies.txt \
  -w "%{http_code}" \
  -s -o /dev/null)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Test 2 PASSED"
else
  echo "❌ Test 2 FAILED (HTTP $HTTP_CODE)"
fi

# Test 3: Auth check without cookie
echo "Test 3: Auth check without cookie..."
HTTP_CODE=$(curl -X GET "$BASE_URL/api/auth/me" \
  -w "%{http_code}" \
  -s -o /dev/null)

if [ "$HTTP_CODE" = "401" ]; then
  echo "✅ Test 3 PASSED"
else
  echo "❌ Test 3 FAILED (Expected 401, got $HTTP_CODE)"
fi

# Test 4: Test cookie endpoint
echo "Test 4: Cookie debug endpoint..."
RESPONSE=$(curl -X GET "$BASE_URL/api/auth/test-cookie" \
  --cookie cookies.txt \
  -s)

if echo "$RESPONSE" | grep -q '"cookie_present":true'; then
  echo "✅ Test 4 PASSED"
else
  echo "❌ Test 4 FAILED"
fi

# Test 5: Protected endpoint
echo "Test 5: Protected endpoint with cookie..."
HTTP_CODE=$(curl -X GET "$BASE_URL/api/files/list" \
  --cookie cookies.txt \
  -w "%{http_code}" \
  -s -o /dev/null)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Test 5 PASSED"
else
  echo "❌ Test 5 FAILED (HTTP $HTTP_CODE)"
fi

# Test 6: Logout
echo "Test 6: Logout deletes cookie..."
HTTP_CODE=$(curl -X POST "$BASE_URL/api/auth/logout" \
  --cookie cookies.txt \
  --cookie-jar cookies.txt \
  -w "%{http_code}" \
  -s -o /dev/null)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Test 6 PASSED"
else
  echo "❌ Test 6 FAILED (HTTP $HTTP_CODE)"
fi

# Test 7: Auth fails after logout
echo "Test 7: Auth fails after logout..."
HTTP_CODE=$(curl -X GET "$BASE_URL/api/auth/me" \
  --cookie cookies.txt \
  -w "%{http_code}" \
  -s -o /dev/null)

if [ "$HTTP_CODE" = "401" ]; then
  echo "✅ Test 7 PASSED"
else
  echo "❌ Test 7 FAILED (Expected 401, got $HTTP_CODE)"
fi

echo "=========================================="
echo "🎉 Integration tests complete!"
```

**Save as:** `test_sso_cookie.sh`

**Run:**
```bash
chmod +x test_sso_cookie.sh
./test_sso_cookie.sh
```

---

## ✅ Acceptance Criteria

### Backend
- [ ] Login sets HttpOnly cookie
- [ ] Register sets HttpOnly cookie
- [ ] Logout deletes cookie
- [ ] `/auth/me` works with cookie
- [ ] All protected endpoints work with cookie
- [ ] CORS allows credentials
- [ ] Cookie domain is shared (192.168.124.50)
- [ ] Cookie properties correct (HttpOnly, SameSite, etc)

### Frontend
- [ ] Login Portal sets cookie
- [ ] EuCloud uses cookie for auth
- [ ] EuType uses cookie for auth
- [ ] EuSheets uses cookie for auth
- [ ] Cookie automatically sent with requests
- [ ] Logout deletes cookie everywhere
- [ ] No localStorage token needed

### Security
- [ ] HttpOnly prevents JavaScript access
- [ ] SameSite prevents CSRF
- [ ] Token expires after 24 hours
- [ ] 401 redirects to login
- [ ] Cookie domain restricted

### User Experience
- [ ] Login once → access all apps
- [ ] No repeated logins
- [ ] Logout once → logged out everywhere
- [ ] Seamless app switching
- [ ] Professional SSO flow

---

## 📈 Success Metrics

- ✅ **0** localStorage tokens
- ✅ **1** cookie for all apps
- ✅ **0** login prompts when switching apps
- ✅ **100%** cookie-based authentication
- ✅ **0** XSS vulnerabilities
- ✅ **0** CSRF vulnerabilities

---

## 📚 Documentation

- [Backend SSO Implementation](./BACKEND_SSO_IMPLEMENTATION.md)
- [Frontend SSO Integration](./SSO_INTEGRATION.md)
- [SSO Architecture](./SSO_ARCHITECTURE.md)

---

**Last Updated:** November 18, 2025  
**Status:** Ready for Testing
