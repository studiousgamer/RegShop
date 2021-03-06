from pymongo import MongoClient
from uuid import uuid4
import random
import datetime
import requests

class Database:
    def __init__(self, URL):
        self.client = MongoClient(URL)
        self.db = self.client.RegShop
        self.users = self.db.users
        self.shops = self.db.shops
        
    def addUser(self, user):
        id =str(uuid4())
        self.users.insert_one({
            '_id': id,
            'username': user['name'],
            'email': user['email'],
            'shops': [],
            'created': datetime.datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
        })
    
    def userExists(self, email):
        return self.users.find_one({'email': email}) is not None
    
    def getUser(self, email):
        return self.users.find_one({'email': email})
    
    def getUserWithId(self, id):
        return self.users.find_one({'_id': id})

    def getUserShops(self, id):
        shops = self.users.find_one({'_id': id})['shops']
        return [self.shops.find_one({'_id': shop}) for shop in shops]

    def addShop(self, name, description, user):
        shop = {
            '_id': "".join(random.choice("1234567890") for i in range(5)),
            'name': name,
            'description': description,
            'owner': user['_id'],
            'items': [],
            'receipts': [],
            'created': datetime.datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
        }
        self.shops.insert_one(shop)
        self.users.update_one({'_id': user['_id']}, {'$push': {'shops': shop['_id']}})

    def getShop(self, id):
        return self.shops.find_one({'_id': id})
    
    def addItem(self, shop, name, price):
        items = shop['items']
        item = {
            '_id': "".join(random.choice("1234567890") for i in range(5)),
            'name': name,
            'price': price,
            'created': datetime.datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
        }
        self.shops.update_one({'_id': shop['_id']}, {'$push': {'items': item}})

    def deleteItem(self, shop, item_id):
        self.shops.update_one({'_id': shop['_id']}, {'$pull': {'items': {'_id': item_id}}})

    def createReceipt(self, shop, items):
        final = []
        for item in items:
            quantity = items[item]
            for i in shop['items']:
                if i['name'] == item:
                    price = i['price']
                    break
            total = float(quantity) * price
            name = item
            data = {
                "name": name,
                "quantity": quantity,
                "price": price,
                "total": total
            }
            final.append(data)
        total_price = sum([i['total'] for i in final])
        receipt = {
            '_id': "".join(random.choice("1234567890") for i in range(5)),
            'items': final,
            'total': total_price,
            'created': datetime.datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
        }
        self.shops.update_one({'_id': shop['_id']}, {'$push': {'receipts': receipt}})