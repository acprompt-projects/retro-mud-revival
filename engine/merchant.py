class Shop:
    def __init__(self, shop_id, inventory):
        self.id = shop_id
        self.inventory = inventory  # {item_id: price}
    
    def has_item(self, item_id):
        return item_id in self.inventory
    
    def get_price(self, item_id):
        return self.inventory.get(item_id, 0)
    
    def list_goods(self, item_manager):
        lines = ["【商品列表】"]
        for iid, price in self.inventory.items():
            name = item_manager.get_name(iid)
            lines.append(f"  {name}: {price} 铜币")
        return "\n".join(lines)

SHOPS = {
    "blacksmith_wang": Shop("blacksmith_wang", {
        "rusty_sword": 10,
        "steel_sword": 50
    }),
    "tavern_boss": Shop("tavern_boss", {
        "bread": 2,
        "healing_potion": 5
    }),
    "traveling_merchant": Shop("traveling_merchant", {
        "bread": 3,
        "healing_potion": 8,
        "magic_dagger": 30
    })
}
