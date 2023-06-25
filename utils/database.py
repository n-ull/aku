from pymongo import MongoClient

# import os
# MONGO_URI = "mongodb+srv://akuowner:VbXxlg1br3dCa9yQ@akucluster.c2cirfo.mongodb.net/?retryWrites=true&w=majority"


class AkuDatabase:
    def __init__(self, uri) -> None:
        self.client = MongoClient(uri)
        self.user_collection = self.client["aku_bot"]["users"]

    async def add_uno_win(self, user_id: int):
        self.user_collection.find_one_and_update({"id": user_id}, {"$inc": {"wins": 1}}, upsert=True)

    async def add_uno_game(self, user_id: int):
        self.user_collection.find_one_and_update({"id": user_id}, {"$inc": {"games": 1}}, upsert=True)

    async def uno_wins(self, user_id: int):
        return self.user_collection.find_one({"id": user_id})
