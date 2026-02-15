import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    base_url: str = "https://anc.apm.activecommunities.com/santamonicarecreation/rest"
    session_cookie: str = ""
    csrf_token: str = ""

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
