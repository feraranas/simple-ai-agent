from pathlib import Path
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).parent
## __file__ : '/home/user/project/script.py'
## Path(__file__) : Path('/home/user/project/script.py')
## Path(__file__).parent : '/home/user/project'
## ROOT_DIR = /home/user/project

class Settings(BaseSettings):

    OPENCHARGEMAP_API_KEY: str
    MARKETSTACK_API_KEY: str
    OPENAI_API_KEY: str
    STORAGE_FILE_PATH: Path = ROOT_DIR / "data.csv"
    ## db_host: str
    ## db_port: int = 5432
    ## use_ssl: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
