import os
import requests as http_requests
from functools import wraps
from flask import jsonify, request, g
import logging

KEYCLOAK_URL = os.environ.get('KEYCLOAK_URL', 'http://keycloak:8080')
KEYCLOAK_REALM = os.environ.get('KEYCLOAK_REALM', 'photo-search')

def verify_keycloak_token(token):
    """Verify Keycloak token and return user info."""
    try:
        userinfo_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
        headers = {'Authorization': f'Bearer {token}'}
        response = http_requests.get(userinfo_url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logging.error(f"Keycloak verification error: {str(e)}")
        return None

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(' ')[1]
        user_info = verify_keycloak_token(token)

        if not user_info:
            return jsonify({"error": "Invalid or expired token"}), 401

        g.user_id = user_info.get('sub')
        g.user_info = user_info
        g.roles = user_info.get("realm_access", {}).get("roles", [])
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        
        if "admin" not in g.roles:
            return jsonify({"error": "Unauthorized", "roles": g.user_info}), 403

        return f(*args, **kwargs)

    return decorated