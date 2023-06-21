import base64
import math
import random
import discord
from urllib.parse import quote
from discord.interactions import Interaction

domainpath: str = "jackblack-generatior.glitch.me/v2"

class Card:
    suits = ["♠", "♣", "♦", "♥"]

    def __init__(self, index):
        self.index : int = index
        self.value : int = (self.index % 13) + 1
    
    def __str__(self):
        return f"{self.value} of {self.suits[math.floor(self.index / 13)]}"
    
    def get_rank(self) -> str:
        if(self.value == 1 | self.value == 11 | self.value == 12 | self.value == 13):
            rank_dict = {
                1: "Ace",
                11: "Jack",
                12: "Queen",
                13: "King"
            }

            return rank_dict[self.value]
        else:
            return str(self.value)
        

class Deck:
    def __init__(self):
        self.cards: list[Card] = []
        self.generate_deck()

    def generate_deck(self):
        self.cards = [Card(index) for index in range(52)]
    
    def deal_card(self) -> Card:
        return self.cards.pop()

class Hand:
    def __init__(self) -> None:
        self.cards : list[Card] = []

    def add_card(self, card):
        self.cards.append(card)
    
    def list_of_indexes(self):
        self.list: list[str] = []
        for card in self.cards:
            self.list.append(str(card.index))
        return self.list
    
    def get_value(self) -> int:
        value = 0
        has_ace = False
        for card in self.cards:
            if card.value == 1:
                value += 11
                has_ace = True
            elif card.value >= 10:
                value += 10
            else:
                value += card.value
        
        if has_ace and value > 21:
            value -= 10
        
        return value
       
class Blackjack():
    def __init__(self, player_id: int, player: discord.User):
        self.deck = Deck()
        self.player = player
        self.player_id = player_id
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.status = "Playing"
        self.setup_game()
    
    def play(self, instruction: str):
        if(instruction == "hit"):
            self.player_hand.add_card(self.deck.deal_card())
            if self.player_hand.get_value() > 21:
                self.status = "Lose"
                return self.game_embed("stand")
            else:
                return self.get_player_hand_status()
        elif(instruction == "stand"):
            self.dealer_play()
            return self.get_final_result()
    
    def dealer_play(self):
        while self.dealer_hand.get_value() < 17:
            self.dealer_hand.add_card(self.deck.deal_card())

    def setup_game(self):
        random.shuffle(self.deck.cards)
        self.player_hand.add_card(self.deck.deal_card())
        self.player_hand.add_card(self.deck.deal_card())
        self.dealer_hand.add_card(self.deck.deal_card())
        self.dealer_hand.add_card(self.deck.deal_card())
    
    def get_player_hand_status(self):
        player_hand_status = "Your hand:\n"
        for card in self.player_hand.cards:
            player_hand_status += str(card) + "\n"
        player_hand_status += "Total value: " + str(self.player_hand.get_value())
        return self.game_embed()
    
    def get_final_result(self):
        final_result = "Final Result\n"
        for card in self.player_hand.cards:
            final_result += str(card) + "\n"
        final_result += "Total value: " + str(self.player_hand.get_value()) + "\n\n"
        final_result += "Dealer's hand:\n"
        for card in self.dealer_hand.cards:
            final_result += str(card) + "\n"
        final_result += "Total value: " + str(self.dealer_hand.get_value()) + "\n\n"

        player_value = self.player_hand.get_value()
        dealer_value = self.dealer_hand.get_value()

        if player_value > 21:
            final_result += "You bust! Dealer wins."
            self.status = "Lose"
        elif dealer_value > 21:
            final_result += "Dealer busts! You win."
            self.status = "Win"
        elif player_value > dealer_value:
            final_result += "You win!"
            self.status = "Win"
        elif dealer_value > player_value:
            final_result += "Dealer wins!"
            self.status = "Lose"
        else:
            final_result += "It's a tie!"
            self.status = "Tie"

        return self.game_embed("stand")
    
    def encode_cards(self, isStand: bool = False):
        decoded = ""
        separator = "/"
        decoded += separator.join(self.player_hand.list_of_indexes())
        decoded += "-"
        if(isStand):
            decoded += separator.join(self.dealer_hand.list_of_indexes())
        elif(isStand == False):
            decoded += str(self.dealer_hand.cards[0].index)
            decoded += "/52"
        encoded_string = base64.b64encode(decoded.encode())
        encoded_string = encoded_string.decode()
        escaped_string = quote(encoded_string)
        return escaped_string

    def generate_image_link(self) -> str:
        if self.status == "Playing":
            return f"https://{domainpath}/{self.encode_cards(isStand=False)}"
        else:
            return f"https://{domainpath}/{self.encode_cards(isStand=True)}"
    
    def game_embed(self, instruction: str = "play") -> discord.Embed:
        match self.status:
            case "Playing":
                color = discord.Colour.dark_gray()
            case "Lose":
                color = discord.Colour.brand_red()
            case "Tie":
                color = discord.Colour.orange()
            case "Win":
                color = discord.Colour.brand_green()
        
        embed = discord.Embed(color=color)
        embed.set_author(name=self.player.display_name, icon_url=self.player.avatar)
        if instruction == "play":
            embed.add_field(name="Your cards:", value=f"```{self.player_hand.get_value()}```", inline=True)
            embed.add_field(name="Dealer cards:", value=f"```???```", inline=True)
            embed.set_image(url=self.generate_image_link())
        elif instruction == "stand":
            embed.add_field(name=f"Your result is:", value=f"{self.status}", inline=False)
            embed.add_field(name="Your cards:", value=f"```{self.player_hand.get_value()}```", inline=True)
            embed.add_field(name="Dealer cards:", value=f"```{self.dealer_hand.get_value()}```",inline=True)
            embed.set_image(url=self.generate_image_link())
        return embed

            
class GameView(discord.ui.View):

    message : discord.WebhookMessage
    game : Blackjack

    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
    
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.message.edit(embed=self.game.play('hit'))

        if(self.game.status == "Lose"):
            await self.disable_all_items()
            self.stop()
        
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.message.edit(embed=self.game.play('stand'))
        await self.disable_all_items()
        self.stop()
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.game.player_id:
            await interaction.response.send_message("You are not playing this game, fuck off bitch.", ephemeral=True)
            return False
        else:
            return True
