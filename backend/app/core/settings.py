from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    DATABASE_URL: str | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None

    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRES_MIN: int
    REFRESH_TOKEN_EXPIRES_DAYS: int

    # Integração Betha
    BETHA_WSDL_URL: str = "https://nota-eletronica.betha.cloud/dps/ws"
    BETHA_ENV: str = "2"
    BETHA_SERIE: str = "900"
    BETHA_POLL_INTERVAL_S: int = 5
    BETHA_POLL_MAX_ATTEMPTS: int = 12
    BETHA_CERT_PATH: str | None = None
    BETHA_CERT_PASSWORD: str | None = None
    BETHA_LOG_DIR: str = "betha_logs"

    # Constantes do prestador Brand Open
    EMITTER_CNPJ: str = "11222333000181"
    EMITTER_PHONE: str | None = None
    EMITTER_EMAIL: str | None = None
    CITY_CODE: str = "4204608"

    # Constantes fixas de tributo do prestador.
    # SERVICE_CODE/NBS_CODE/TAX_RATE/TRIB_ISSQN/RET_ISSQN foram aposentados: agora
    # vêm do snapshot `recurrence.inf_dps` (ver xml_builder). Permanecem aqui apenas
    # as constantes do regime do prestador e os totais aproximados (totTrib).
    OP_SIMP_NAC: str = "3"
    REG_AP_TRIB_SN: str = "2"
    REG_ESP_TRIB: str = "0"
    TOT_TRIB_FED: str = "0.00"
    TOT_TRIB_EST: str = "0.00"
    TOT_TRIB_MUN: str = "0.00"

    # Cron e SMTP
    CRON_SECRET: str | None = None

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True
    NOTIFICATION_EMAIL: str | None = None
    NOTIFICATION_FROM: str | None = None

    @property
    def sqlalchemy_database_uri(self) -> str:
        """
        Constrói a URI de conexão do SQLAlchemy com base nas configurações fornecidas.
        """

        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            "postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()  # type: ignore[call-arg]
