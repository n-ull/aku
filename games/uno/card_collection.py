from discord import Emoji

from game_base import CardCollection

from .card import UnoCard


class UnoDeck(CardCollection):
    def __init__(self):
        super().__init__()

    def generate_deck(self):
        colors = ["R", "G", "B", "Y"]
        values = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "SKIP", "REVERSE", "+2"]
        for color in colors:
            for value in values:
                self.cards.append(UnoCard(color, value))
                self.cards.append(UnoCard(color, value))
        for x in range(4):
            self.cards.append(UnoCard("WILD", "WILD"))
            self.cards.append(UnoCard("WILD", "WILD+4"))

    def pop_card(self) -> UnoCard:
        return self.cards.pop()

    def pop_multiple_cards(self, quantity: int) -> list[UnoCard]:
        popped_cards: list[UnoCard] = []
        for x in range(quantity):
            card = self.cards.pop()
            popped_cards.append(card)
        return popped_cards


class UnoHand(CardCollection):
    def __init__(self):
        super().__init__()

    def get_card_by_id(self, id: str) -> UnoCard | None:
        card = next((c for c in self.cards if c.id == int(id)), None)
        return card

    def emoji_hand(self, emoji_col: list[Emoji]):
        string = ""
        for card in self.cards:
            emoji = next((e for e in emoji_col if e.name == f"{card.emoji_name}"), "Carta")
            string += f"{emoji} "
        return string if len(string) > 2 else "Out of cards!"

    def generate_valid_hand(self, last_card: UnoCard) -> list[UnoCard]:
        cards: list[UnoCard] = []
        for card in self.cards:
            if card.validate(last_card):
                cards.append(card)
        return cards

    def generate_plus_hand(self):
        cards: list[UnoCard] = []
        for card in self.cards:
            if card.value == "+2":
                cards.append(card)
        return cards
