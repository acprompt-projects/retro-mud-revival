from .items import ItemManager
from .quests import QuestLog

class Player:
    def __init__(self, name, writer):
        self.name = name
        self.writer = writer
        self.room_id = "village_square"
        self.hp = 100
        self.max_hp = 100
        self.attack = 5
        self.defense = 2
        self.inventory = []
        # Equipment slots: weapon / armor / shield / accessory
        self.equipped = {
            'weapon':    None,
            'armor':     None,
            'shield':    None,
            'accessory': None,
        }
        self.in_combat = False
        self.combat_target = None
        self.exp = 0
        self.level = 1
        self.gold = 10
        self.quest_log = QuestLog()

    def send(self, text):
        if self.writer:
            self.writer.write((text + "\n").encode('utf-8'))
        else:
            # Agent gateway mode: buffer messages
            if not hasattr(self, 'message_buffer'):
                self.message_buffer = []
            self.message_buffer.append(text)

    def send_line(self, text=""):
        self.send(text)

    def take_damage(self, amount):
        actual = max(1, amount - self.get_total_defense())
        self.hp -= actual
        return actual

    def heal(self, amount):
        old = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old

    def is_alive(self):
        return self.hp > 0

    def add_item(self, item_id):
        self.inventory.append(item_id)

    def remove_item(self, item_id):
        if item_id in self.inventory:
            self.inventory.remove(item_id)
            # Unequip if equipped in any slot
            for slot, eid in self.equipped.items():
                if eid == item_id:
                    self.equipped[slot] = None
            return True
        return False

    def has_item(self, item_id):
        return item_id in self.inventory

    def add_exp(self, amount):
        self.exp += amount
        # Level up every 100 exp
        new_level = 1 + self.exp // 100
        if new_level > self.level:
            old_level = self.level
            self.level = new_level
            self.max_hp += 20
            self.hp = self.max_hp
            self.attack += 2
            self.defense += 1
            return True, old_level, new_level
        return False, self.level, self.level

    def get_total_attack(self):
        base = self.attack
        im = ItemManager()
        # Weapon slot bonus
        w = self.equipped.get('weapon')
        if w:
            item = im.get(w)
            if item:
                base += item.get('attack_bonus', 0)
        # Accessory slot bonus
        acc = self.equipped.get('accessory')
        if acc:
            item = im.get(acc)
            if item:
                base += item.get('attack_bonus', 0)
        return base

    def get_total_defense(self):
        base = self.defense
        im = ItemManager()
        for slot in ('armor', 'shield', 'accessory'):
            eid = self.equipped.get(slot)
            if eid:
                item = im.get(eid)
                if item:
                    base += item.get('defense_bonus', 0)
        return base

    # ------------------------------------------------------------------
    # Inventory / status display
    # ------------------------------------------------------------------
    _SLOT_LABEL = {
        'weapon':    '武器',
        'armor':     '护甲',
        'shield':    '盾牌',
        'accessory': '饰品',
    }

    def get_inventory_desc(self, item_manager):
        lines = []
        # Equipped summary
        any_equipped = any(self.equipped.values())
        if any_equipped:
            lines.append("【装备栏】")
            for slot, label in self._SLOT_LABEL.items():
                eid = self.equipped.get(slot)
                if eid:
                    ename = item_manager.get_name(eid)
                    lines.append(f"  {label}: {ename}")
                else:
                    lines.append(f"  {label}: (空)")
        # Bag
        if not self.inventory:
            lines.append("你的背包是空的。")
        else:
            lines.append("【背包】")
            for iid in self.inventory:
                item = item_manager.get(iid)
                name = item['name'] if item else iid
                # Mark all equipped slots
                eq_slots = [self._SLOT_LABEL[s] for s, e in self.equipped.items() if e == iid]
                marker = f" [装备中-{'/'.join(eq_slots)}]" if eq_slots else ""
                lines.append(f"  - {name}{marker}")
        return "\n".join(lines)

    def get_status_desc(self):
        im = ItemManager()
        lines = [
            f"【状态】",
            f"姓名: {self.name} | 等级: {self.level}",
            f"生命: {self.hp}/{self.max_hp} | 经验: {self.exp}",
            f"攻击: {self.get_total_attack()} (基础 {self.attack})"
            + (f" + 装备" if self.get_total_attack() != self.attack else ""),
            f"防御: {self.get_total_defense()} (基础 {self.defense})"
            + (f" + 装备" if self.get_total_defense() != self.defense else ""),
            f"金币: {self.gold}",
        ]
        for slot, label in self._SLOT_LABEL.items():
            eid = self.equipped.get(slot)
            if eid:
                lines.append(f"{label}: {im.get_name(eid)}")
        return "\n".join(lines)
