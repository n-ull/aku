from discord import Member


class Player:
    def __init__(self, user: Member) -> None:
        self.name = user.display_name
        self.id = user.id
        self.warns = 0
