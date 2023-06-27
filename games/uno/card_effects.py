# abstract class for effects
from enum import Enum

class CardEffect:
    def execute(self, game): ...

class PlusTwoEffect(CardEffect):
    def execute(self, game):
        game.stack += 2
class PlusFourEffect(CardEffect):
    def execute(self, game):
        cards = game.deck.pop_multiple_cards(4)
        game.next_player.hand.add_multiple_cards(cards)
        game.skip_turn()
class ReverseEffect(CardEffect):
    def execute(self, game):
        if len(game.players) == 2:
            game.skip_turn()
            game.change_orientation()
        else:
            game.change_orientation()
class SkipEffect(CardEffect):
    def execute(self, game):
        game.skip_turn()

class EffectsEnum(Enum):
    PLUSTWO = PlusTwoEffect()
    REVERSE = ReverseEffect()
    SKIP = SkipEffect()
    PLUSFOUR = PlusFourEffect()