import os
import json
import base64
import firebase_admin

from firebase_admin import credentials, auth, firestore
from fastapi import HTTPException, status, Header

from app.utils.logger import logger

_db = None


# ----------------------------------Firebase Initialization----------------------------------


def initialize_firebase():
    """
    Initializes Firebase Admin SDK exactly once per process.
    Safe to call multiple times.
    """

    # Prevent re-initialization
    if firebase_admin._apps:
        return

    firebase_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_BASE64")

    if not firebase_b64:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON_BASE64 not set")

    try:
        # Decode Base64 -> JSON string
        firebase_json = base64.b64decode(firebase_b64).decode("utf-8")

        # Convert JSON string -> Python dict
        service_account_info = json.loads(firebase_json)

        # Initialize Firebase
        cred = credentials.Certificate(service_account_info)

        firebase_admin.initialize_app(cred)

        logger.info("Firebase initialized successfully")

    except Exception as e:
        logger.error(f"Firebase initialization failed: {str(e)}")

        raise RuntimeError(f"Firebase initialization failed: {str(e)}")


# ----------------------------------Verify Firebase Token----------------------------------


def verify_firebase_token(token: str) -> dict:
    """
    Verifies Firebase ID token and returns decoded claims.
    """

    try:
        initialize_firebase()

        decoded_token = auth.verify_id_token(token)

        print("🔥 Firebase token verified")

        return decoded_token

    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token expired",
        )

    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
        )

    except Exception as e:
        logger.error(f"Firebase auth error: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


# ----------------------------------Get Current User----------------------------------


def get_current_user(authorization: str = Header(...)):
    """
    FastAPI dependency to extract and verify Firebase token.
    """

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = authorization.split(" ")[1]

    return verify_firebase_token(token)


# ----------------------------------Firestore Initialization----------------------------------


def get_firestore():
    """
    Returns Firestore client singleton.
    """

    global _db

    # Reuse existing Firestore client
    if _db is not None:
        return _db

    try:
        # Ensure Firebase initialized
        initialize_firebase()

        # Create Firestore client
        _db = firestore.client()

        logger.info("Firestore initialized successfully")

        return _db

    except Exception as e:
        logger.error(f"Firestore initialization failed: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to initialize Firebase Firestore",
        )
