import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

class ItemManager:
    def __init__(self):
        with open(os.path.join(DATA_DIR, 'items.json'), 'r', encoding='utf-8') as f:
            self.items = json.load(f)
    
    def get(self, item_id):
        return self.items.get(item_id)
    
    def get_name(self, item_id):
        item = self.items.get(item_id)
        return item['name'] if item else item_id
    
    def describe(self, item_id):
        item = self.items.get(item_id)
        if not item:
            return "一个不明物体。"
        desc = f"{item['name']}: {item['description']}"
        if item.get('type') == 'weapon':
            desc += f" [攻击+{item.get('attack_bonus', 0)}]"
        elif item.get('type') == 'consumable':
            desc += f" [恢复{item.get('heal_amount', 0)}生命]"
        return desc
