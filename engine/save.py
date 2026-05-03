import json
import os

SAVE_DIR = os.path.join(os.path.dirname(__file__), '..', 'saves')

class SaveManager:
    def __init__(self):
        os.makedirs(SAVE_DIR, exist_ok=True)

    def save(self, player, world):
        data = {
            "name": player.name,
            "room_id": player.room_id,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "attack": player.attack,
            "defense": player.defense,
            "inventory": player.inventory,
            "equipped": player.equipped,
            "exp": getattr(player, 'exp', 0),
            "level": getattr(player, 'level', 1),
            "gold": getattr(player, 'gold', 0),
            "quest_active": {
                qid: {"completed": q.completed, "target_count": q.target_count}
                for qid, q in player.quest_log.active.items()
            },
            "quest_completed": player.quest_log.completed,
            "world_items": {rid: list(room.items) for rid, room in world.rooms.items()},
            "world_npcs": {
                rid: [npc.id for npc in room.npcs if npc.alive]
                for rid, room in world.rooms.items()
            }
        }
        path = os.path.join(SAVE_DIR, f"{player.name}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def load(self, name, player, world):
        path = os.path.join(SAVE_DIR, f"{name}.json")
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        player.name = data.get('name', name)
        player.room_id = data.get('room_id', 'village_square')
        player.hp = data.get('hp', 100)
        player.max_hp = data.get('max_hp', 100)
        player.attack = data.get('attack', 5)
        player.defense = data.get('defense', 2)
        player.inventory = list(data.get('inventory', []))
        player.gold = data.get('gold', 10)
        player.exp = data.get('exp', 0)
        player.level = data.get('level', 1)

        # Restore equipped — support both old (equipped_weapon str) and new (equipped dict)
        blank = {'weapon': None, 'armor': None, 'shield': None, 'accessory': None}
        if 'equipped' in data and isinstance(data['equipped'], dict):
            saved_eq = data['equipped']
            player.equipped = {k: saved_eq.get(k) for k in blank}
        elif 'equipped_weapon' in data:
            # backward compat
            player.equipped = dict(blank)
            player.equipped['weapon'] = data.get('equipped_weapon')
        else:
            player.equipped = dict(blank)

        # Restore quests
        from .quests import QuestLog, QUESTS
        player.quest_log = QuestLog()
        for qid, qdata in data.get('quest_active', {}).items():
            if qid in QUESTS:
                q = player.quest_log.assign(qid)
                if q:
                    q.completed = qdata.get('completed', False)
                    q.target_count = qdata.get('target_count', q.target_count)
        player.quest_log.completed = list(data.get('quest_completed', []))

        # Restore world state
        for rid, items in data.get('world_items', {}).items():
            if rid in world.rooms:
                world.rooms[rid].items = list(items)

        for rid, npc_ids in data.get('world_npcs', {}).items():
            if rid in world.rooms:
                for npc in world.rooms[rid].npcs:
                    npc.alive = npc.id in npc_ids

        return data
