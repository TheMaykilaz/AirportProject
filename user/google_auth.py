from google.oauth2 import id_token
from google.auth.transport import requests


def verify_google_token(id_token_str, client_id):
    """
    Verifies a Google ID token and returns user info.

    Args:
        id_token_str (str): The ID token received from frontend Google login.
        client_id (str): Your Google OAuth2 client ID.

    Returns:
        dict | None: User info dictionary if valid, None if invalid.
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            id_token_str,
            requests.Request(),
            client_id
        )



        return {
            "email": idinfo.get("email"),
            "first_name": idinfo.get("given_name"),
            "last_name": idinfo.get("family_name"),
            "google_sub": idinfo.get("sub")
        }

    except ValueError:
        # Invalid token
        return None
