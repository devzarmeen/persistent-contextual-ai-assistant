from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Persistent Contextual AI Assistant"
    app_env: str = "development"
    debug: bool = True

    database_url: str = "sqlite:///./data/app.db"

    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-3.7-flash"
    gemini_embedding_model: str = "gemini-embedding-2"

    jwt_secret: str = "change-this-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = (
        "http://localhost:8000/api/integrations/google/callback"
    )

    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()