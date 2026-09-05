"""
Central configuration for the backend.
All values are loaded from environment variables / .env file.
Every other module (graph, risk, VASP, blockchain) should read
its connection info from here — never hardcode URLs elsewhere.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SIH26183 Crypto Fraud Backend"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://sih_user:sih_pass@localhost:5432/crypto_fraud_db"

    # Auth
    SECRET_KEY: str = "dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS - comma separated origins, e.g. for Member 5's React dashboard
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Other members' services (Member 1 - Graph, Member 2 - Blockchain data,
    # Member 4 - Risk/ML, Member 6 - VASP). These may run as separate
    # microservices later; until then USE_MOCK_SERVICES returns sample data
    # so the rest of the system (API + frontend) can be developed/demoed now.
    GRAPH_SERVICE_URL: str = "http://localhost:8001"
    BLOCKCHAIN_SERVICE_URL: str = "http://localhost:8002"
    RISK_SERVICE_URL: str = "http://localhost:8003"
    VASP_SERVICE_URL: str = "http://localhost:8004"
    USE_MOCK_SERVICES: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
