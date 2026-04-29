import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from pathlib import Path


class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "tickets_api"
    env: str = "development"
    debug: bool = False
    database_url: str

    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout_seconds: int = 30
    db_pool_recycle_seconds: int = 1800
    db_pool_pre_ping: bool = True

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    payment_link_token_ttl_minutes: int = 180
    frontend_public_url: str = ""

    redis_url: str = ""
    redis_connect_retry_seconds: int = 30
    cache_default_ttl_seconds: int = 300
    allowed_origins: list[str] = []
    cors_allow_origin_regex: str = ""

    gzip_enabled: bool = True
    gzip_minimum_size_bytes: int = 1024
    gzip_compresslevel: int = 6

    rate_limit_enabled: bool = True
    rate_limit_global_requests: int = 120
    rate_limit_global_window_seconds: int = 60
    rate_limit_login_requests: int = 10
    rate_limit_login_window_seconds: int = 60
    rate_limit_create_order_requests: int = 20
    rate_limit_create_order_window_seconds: int = 60
    rate_limit_create_payment_requests: int = 20
    rate_limit_create_payment_window_seconds: int = 60
    rate_limit_get_payment_requests: int = 120
    rate_limit_get_payment_window_seconds: int = 60
    rate_limit_trust_x_forwarded_for: bool = False

    media_root: str = "media"
    media_url_path: str = "/media"
    upload_max_image_size_mb: int = 5

    smtp_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "EventTix"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: int = 20

    crossmint_env: str = "production"
    crossmint_host: str = ""
    crossmint_server_side_api_key: str = ""
    crossmint_client_side_api_key: str = ""
    crossmint_orders_base_url: str = ""
    crossmint_users_base_url: str = ""
    crossmint_recipient_user_email: str = ""
    crossmint_recipient_wallet_address: str = ""
    crossmint_recipient_chain: str = "solana"
    crossmint_token_locator: str = ""
    crossmint_payment_method: str = "checkoutcom-flow"
    crossmint_support_whatsapp: str = ""

    @model_validator(mode="after")
    def _validate_production_security(self):
        env = str(self.env or "").strip().lower()
        if env != "production":
            return self

        jwt_secret = str(self.jwt_secret_key or "").strip()
        if len(jwt_secret) < 32:
            raise ValueError("JWT_SECRET_KEY debe tener al menos 32 caracteres en produccion")

        if self.debug:
            raise ValueError("DEBUG debe ser false en produccion")

        if any(str(origin).strip() == "*" for origin in self.normalized_allowed_origins):
            raise ValueError("ALLOWED_ORIGINS no puede contener '*' en produccion")

        regex = str(self.cors_allow_origin_regex or "").strip()
        if regex in {".*", "^.*$", "(.+)"}:
            raise ValueError("CORS_ALLOW_ORIGIN_REGEX es demasiado permisivo en produccion")

        if not self.normalized_allowed_origins and not regex:
            raise ValueError(
                "Configura ALLOWED_ORIGINS o CORS_ALLOW_ORIGIN_REGEX en produccion"
            )

        frontend_url = str(self.frontend_public_url or "").strip().rstrip("/")
        if frontend_url and not frontend_url.startswith("https://"):
            raise ValueError("FRONTEND_PUBLIC_URL debe usar https en produccion")

        return self

    @property
    def normalized_allowed_origins(self) -> list[str]:
        raw = self.allowed_origins
        values: list[str] = []

        if isinstance(raw, str):
            text = raw.strip()
            if text:
                try:
                    parsed = json.loads(text)
                except Exception:
                    parsed = [part.strip() for part in text.split(",") if part.strip()]
                if isinstance(parsed, list):
                    values = [str(item) for item in parsed]
                else:
                    values = [str(parsed)]
        elif isinstance(raw, (list, tuple, set)):
            values = [str(item) for item in raw]

        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            origin = str(value or "").strip().rstrip("/")
            if not origin or origin in seen:
                continue
            seen.add(origin)
            normalized.append(origin)

        return normalized

    @property
    def media_root_path(self) -> Path:
        return Path(self.media_root).expanduser().resolve()

    @property
    def normalized_media_url_path(self) -> str:
        raw = str(self.media_url_path or "media").strip()
        return f"/{raw.strip('/')}"

    @property
    def smtp_is_configured(self) -> bool:
        return bool(
            self.smtp_enabled
            and self.smtp_host
            and self.smtp_port > 0
            and self.smtp_from_email
            and self.smtp_username
            and self.smtp_password
        )

settings = Settings()