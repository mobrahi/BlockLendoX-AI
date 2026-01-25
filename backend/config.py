from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

# Get the absolute path to the .env file in the backend folder
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    # These names MUST match your .env keys (case-insensitive)
    rpc_url: str = "http://127.0.0.1:8545"
    chain_id: int = 1337
    contract_address: str = ""
    private_key: str = ""
    secret_key: str = "supersecret"
    database_url: str = "sqlite:///./sql_app.db"
    
    # This tells Pydantic where to look for the file
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        extra='ignore'  # This tells Pydantic: "If you see extra stuff in .env, just ignore it"
    )

@lru_cache()
def get_settings():
    """Returns a cached version of the settings so we don't re-read the file every time."""
    return Settings()