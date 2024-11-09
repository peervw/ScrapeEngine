from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Add your configuration settings here
    # For example:
    auth_token: str = ""
    # Add other configuration variables as needed

def get_settings() -> Settings:
    return Settings()
