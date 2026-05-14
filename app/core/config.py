from pydantic import BaseModel
from datetime import timedelta


class Settings(BaseModel):
    PROJECT_NAME: str = "WorkForce 360 API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Enterprise-grade API with versioning, auth, and custom OpenAPI"
    SECRET_KEY: str = "SUPER_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Test database URL
    # DATABASE_URL: str = (
    #     "postgresql://postgres:Pavithiran2310@workforce360-instance.curgq86s4mqi.us-east-1.rds.amazonaws.com:5432/workforce360_db"
    # )
    # production database URL
    DATABASE_URL: str = (
        "postgresql://postgres:workforce360app@workforce360-instance.cruc6cccuae4.ap-south-2.rds.amazonaws.com:5432/workforce360_db"
    )
    # password - workforce360app

    # FIREBASE_SERVICE_ACCOUNT_PATH: str = "workforce360_firebase_server_account_key.json"


settings = Settings()
