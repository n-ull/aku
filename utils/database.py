from pymongo import MongoClient
import settings

class DBHandler:
    def __init__(self, db_name, collection_name):
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None

    def connect(self):
        self.client = MongoClient(settings.MONGO_URI)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

    def disconnect(self):
        if self.client:
            self.client.close()

    def increment_wins(self, user_id):
        self.collection.update_one({"user_id": user_id}, {"$inc": {"wins": 1}}, upsert=True)

    def increment_games(self, user_id):
        self.collection.update_one({"user_id": user_id}, {"$inc": {"games": 1}}, upsert=True)

    def get_stats(self, user_id):
        user_stats = self.collection.find_one({"user_id": user_id}, {"_id": 0, "wins": 1, "games": 1})
        if user_stats:
            return user_stats.get("wins", 0), user_stats.get("games", 0)
        else:
            return None