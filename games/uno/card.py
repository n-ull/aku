from enum import Enum
import random
from typing import TypeVar

CardType = TypeVar('CardType', bound='Card')

class Card:
    def __init__(self, color: str, value: str) -> None:
        self.color: str = color
        self.value: str = value
        self.id = random.randint(0, 2000)

    def validate(self, card: CardType):
        return self.color == card.color or self.value == card.value or self.is_wild

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
        return f"https://raw.githubusercontent.com/Ratismal/UNO/master/cards/{self.color}{self.value}.png"

    @property
    def name(self) -> str:
        color_name: dict = {
            "R": "Red",
            "B": "Blue",
            "Y": "Yellow",
            "G": "Green"
        }
        return f"{color_name.get(self.color,'Wild')} {self.value}"

    def __str__(self) -> str:
        return f"{self.color}{self.value}"

class CardFilterFunctions:
    def __init__(self) -> None:
        filters = {
            1: self.plus_two_filter,
            2: self.no_effect_win_filter
        }

    def filter(self, filter_value:int, cards: list[Card], last_card: Card) -> list[Card] | None:
        return self.filters.get(filter_value, None)(cards, last_card)
    
    def plus_two_filter(self, cards: list[Card], last_card) -> list[Card] | None:
        new_hand = []
        for card in cards:
            if card.value == "+2": new_hand.append(card)
        return new_hand
                
    def no_effect_win_filter(self, cards: list[Card], last_card) -> list[Card] | None:
        new_hand = []
        for card in cards:
            if not card.has_effect: new_hand.append(card) and card.validate(last_card)
        return new_hand

class CardFilter(Enum):
    PLUS_TWO_STACK = 1
    NO_EFFECT_WIN = 2