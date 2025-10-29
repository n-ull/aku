import discord
import logging
import os
import pathlib
from logging.config import dictConfig

from envsqare import Environment
from envsqare.casters import ListCaster


env = Environment()
env.read_env()
env.casters['LIST_INT'] = ListCaster(splitter=',', element_caster=int)


DEBUG = env.BOOL("DEBUG", True)
MONGO_URI = env("MONGO_URI", "mongodb://localhost:27017/aku")
DISCORD_API_TOKEN = env("DISCORD_API_TOKEN")
TEST_GUILDS = tuple(discord.Object(id=guild_id) for guild_id in env.LIST_INT("TEST_GUILD_IDS"))

BASE_DIR = pathlib.Path(__file__).parent
COGS_DIR = BASE_DIR / "cogs"
SCMD_DIR = BASE_DIR / "slashcmds"

LOGGING_CONFIG = {
    "version": 1,
    "disabled_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)-10s - %(asctime)s - %(module)-15s : %(message)s"
        },
        "standard": {"format": "%(levelname)-10s - %(name)-15s : %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "console2": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/infos.log",
            "mode": "w",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "bot": {"handlers": ["console"], "level": logging.DEBUG if DEBUG else logging.INFO, "propagate": False},
        "discord": {
            "handlers": ["console2", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "game": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "discord": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

dictConfig(LOGGING_CONFIG)
