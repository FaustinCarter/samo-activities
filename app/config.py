import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    base_url: str = "https://anc.apm.activecommunities.com/santamonicarecreation/rest"
    locale: str = "en-US"
    page_size: int = 20
    host: str = "0.0.0.0"
    port: int = 8000
    original_site_link: str = "https://anc.apm.activecommunities.com/santamonicarecreation/activity/search"

    @property
    def base_site_url(self) -> str:
        """Derive the site URL by stripping the ``/rest`` suffix from *base_url*."""
        return self.base_url.removesuffix("/rest")

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
