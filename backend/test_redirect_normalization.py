"""
Test Redirect Normalization

Demonstreert hoe de normalize_redirect() functie verschillende inputs afhandelt.
"""

from routes.auth import normalize_redirect


def test_redirect_normalization():
    """Test verschillende redirect scenarios"""
    
    print("=" * 60)
    print("REDIRECT NORMALIZATION TESTS")
    print("=" * 60)
    
    test_cases = [
        # (input, expected, description)
        (None, "/dashboard", "None → default"),
        ("", "/dashboard", "Empty string → default"),
        ("   ", "/dashboard", "Whitespace → default"),
        
        # Valid relative paths
        ("/dashboard", "/dashboard", "Valid: /dashboard"),
        ("/eutype", "/eutype", "Valid: /eutype"),
        ("/cloud", "/cloud", "Valid: /cloud"),
        ("/api/files", "/api/files", "Valid: nested path"),
        
        # Invalid: absolute URLs (security risk!)
        ("http://evil.com/steal", "/dashboard", "BLOCKED: absolute HTTP URL"),
        ("https://malicious.site", "/dashboard", "BLOCKED: absolute HTTPS URL"),
        ("//evil.com/phishing", "/dashboard", "BLOCKED: protocol-relative URL"),
        
        # Invalid: non-relative paths
        ("dashboard", "/dashboard", "BLOCKED: missing leading /"),
        ("eutype/files", "/dashboard", "BLOCKED: missing leading /"),
        
        # Invalid: path traversal attempts
        ("/../etc/passwd", "/dashboard", "BLOCKED: path traversal .."),
        ("/dashboard/../../secrets", "/dashboard", "BLOCKED: path traversal in path"),
        ("/api//files", "/dashboard", "BLOCKED: double slashes"),
        
        # Edge cases
        ("/", "/", "Valid: root path"),
        ("/dashboard?query=test", "/dashboard", "Valid: with query string (stripped)"),
    ]
    
    passed = 0
    failed = 0
    
    for input_val, expected, description in test_cases:
        result = normalize_redirect(input_val)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status}: {description}")
        print(f"  Input:    {repr(input_val)}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = test_redirect_normalization()
    exit(0 if success else 1)
