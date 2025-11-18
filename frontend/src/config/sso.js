// SSO Configuration for EuCloud
// Deze waarden moeten overeenkomen met je deployment

export const SSO_CONFIG = {
  // EUsuite Login Portal URL
  LOGIN_PORTAL_URL: 'http://192.168.124.50:30090/login',
  
  // Auth check endpoint (voor SSO cookie verificatie)
  AUTH_CHECK_URL: 'http://192.168.124.50:30500/api/auth/me',
  
  // Current app URL (EuCloud)
  APP_URL: 'http://192.168.124.50:30500',
  
  // Cookie settings
  COOKIE_NAME: 'session',
  COOKIE_DOMAIN: '192.168.124.50'
}

// Helper function om redirect URL te bouwen
export const buildLoginRedirectUrl = (returnUrl = null) => {
  const redirectTo = returnUrl || window.location.href
  return `${SSO_CONFIG.LOGIN_PORTAL_URL}?redirect=${encodeURIComponent(redirectTo)}`
}

// Helper function om te checken of cookie bestaat (client-side check)
export const hasSessionCookie = () => {
  return document.cookie.split(';').some(cookie => 
    cookie.trim().startsWith(`${SSO_CONFIG.COOKIE_NAME}=`)
  )
}

export default SSO_CONFIG
