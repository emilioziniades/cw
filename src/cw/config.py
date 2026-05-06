from pathlib import Path

from platformdirs import user_cache_path, user_data_path


class Config:
    app_name: str = "cw"

    @property
    def cache_dir(self) -> Path:
        return user_cache_path(self.app_name)

    @property
    def data_dir(self) -> Path:
        return user_data_path(self.app_name)

    @property
    def database_file(self) -> Path:
        return self.data_dir / "cw.sqlite"


config = Config()
