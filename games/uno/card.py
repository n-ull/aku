from enum import Enum
import random
from discord import Emoji
from typing import TypeVar
import discord

from .card_effects import EffectsEnum

CardType = TypeVar('CardType', bound='Card')

class Card:
    def __init__(self, color: str, value: str) -> None:
        self.color: str = color
        self.value: str = value
        self.id = random.randint(0, 2000)

    def validate(self, card: CardType):
        return self.color == card.color or self.value == card.value or self.is_wild

    @property
    def effect(self):
        effects: dict = {
            "+2": EffectsEnum.PLUSTWO.value,
            "+4": EffectsEnum.PLUSFOUR.value,
            "SKIP": EffectsEnum.SKIP.value,
            "REVERSE": EffectsEnum.REVERSE.value,
        }
        return effects.get(self.value, None)

    @property
    def is_wild(self):
        return self.color == "WILD"

    @property
    def has_effect(self):
        effects: dict = {
            "+2": True,
            "SKIP": True,
            "REVERSE": True
        }
        return effects.get(self.value, False)
    
    @property
    def emoji_name(self):
        effects: dict = {
            "+2": "PLUS2",
            "+4": "PLUS4"
        }

        if self.value == "WILD": return "WILD"
        return f"{self.color}{effects.get(self.value, self.value)}"
    
    @property
    def color_emoji(self) -> str:
        emojis: dict = {
            "R": "🔴",
            "G": "🟢",
            "B": "🔵",
            "Y": "🟡",
        }
        return emojis.get(self.color, "⚫")

    @property
    def color_code(self) -> int:
        colors: dict = {
            "R": 0xff5555,
			"Y": 0xffaa00,
			"G": 0x55aa55,
			"B": 0x5555ff
        }
        return colors.get(self.color, 0x080808)
    
    @property
    def image_url(self) -> str:
        link_card_name = f"{self.color}{self.value}" if not self.is_wild else f"{self.value}"
        if self.value == "+4":
            link_card_name = f"{self.color}WILD+4"
        return f"https://raw.githubusercontent.com/Ratismal/UNO/master/cards/{link_card_name}.png"

    @property
    def name(self) -> str:
        color_name: dict = {
            "R": "RED",
            "B": "BLUE",
            "Y": "YELLOW",
            "G": "GREEN",
        }
        name = f"{color_name.get(self.color, 'COLOR')} {self.value}"
        if self.is_wild:
            name = f"{self.color}"
        return name

    def __str__(self) -> str:
        return f"{self.color}{self.value}"


