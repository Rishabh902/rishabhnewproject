from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Matrimony Platform API"
    environment: str = "development"
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    registration_token_expire_minutes: int = 30
    otp_expire_minutes: int = 5
    otp_max_attempts: int = 5
    frontend_origin: str = "http://localhost:5173"
    public_api_url: str = ""
    admin_login_id: str = ""
    admin_password: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Matrimony Platform"
    password_reset_expire_minutes: int = 30

    upi_vpa: str = ""
    upi_payee_name: str = "MauryaShaadi"

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

settings = Settings()
