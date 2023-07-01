from .card import Card

class CardCollection:
    def __init__(self):
        self.cards: list[Card] = []
    
    def add_card(self, card: Card):
        self.cards.append(card)
    
    def del_card(self, card:Card):
        self.cards.remove(card)
    
    def add_multiple_cards(self, cards: list[Card]):
        self.cards.extend(cards)

    def pop_multiple_cards(self, quantity: int):
        popped_cards: list[Card] = []
        for x in range(quantity):
            card = self.cards.pop()
            popped_cards.append(card)
        return popped_cards

    @property
    def last_card(self) -> Card:
        return self.cards[-1]