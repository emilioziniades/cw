import json
import logging
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path

from platformdirs import user_cache_path, user_config_path, user_data_path

logger = logging.getLogger(__name__)


class OutputStyle(StrEnum):
    PRETTY = auto()
    PLAIN = auto()

    @classmethod
    def default(cls):
        return cls.PRETTY


@dataclass
class UserConfig:
    _path: Path
    output: OutputStyle = OutputStyle.PRETTY

    def __init__(self, path: Path):
        super().__init__()
        self._path = path

        config = self._load_config()

        output = config.get("output")
        self.output = OutputStyle(output) if output else OutputStyle.default()

    def _load_config(self) -> dict:
        try:
            config_raw = self._path.read_text()

            if len(config_raw) == 0:
                return {}

            return json.loads(config_raw)

        except json.JSONDecodeError as ex:
            logger.warning("Failed to decode configuration file. Using default values")
            logger.debug("file=%s, error=%s", self._path, str(ex))
            return {}

        except FileNotFoundError:
            return {}

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

        config = {"output": self.output}
        config_raw = json.dumps(config)

        self._path.write_text(config_raw)


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

    @property
    def config_dir(self) -> Path:
        return user_config_path(self.app_name)

    @property
    def config_file(self) -> Path:
        return self.config_dir / "cw.json"

    @property
    def user_config(self) -> UserConfig:
        return UserConfig(self.config_file)


config = Config()
