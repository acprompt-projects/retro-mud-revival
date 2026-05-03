import json
import os
from .items import ItemManager

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def _load_npcs():
    path = os.path.join(DATA_DIR, 'npcs.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

class NPC:
    def __init__(self, npc_id, data):
        self.id = npc_id
        self.name = data.get('name', npc_id)
        self.description = data.get('description', '')
        self.dialogue = data.get('dialogue', {})
        self.hostile = data.get('hostile', False)
        self.hp = data.get('hp', 20)
        self.max_hp = data.get('max_hp', 20)
        self.attack = data.get('attack', 3)
        self.defense = data.get('defense', 1)
        self.alive = True
        # Patrol fields (lazy tick — advanced on player room entry)
        self.patrol = data.get('patrol', [])           # ordered list of room_ids
        self.patrol_interval = data.get('patrol_interval_seconds', 60)
        self.patrol_index = 0                          # index into self.patrol
        self.last_move_at = 0.0                        # epoch seconds of last move
        self.current_room_id = self.patrol[0] if self.patrol else None

    def get_greeting(self, player=None):
        if player and 'quests' in self.dialogue:
            for qid, quest in player.quest_log.active.items():
                if quest.giver == self.id and qid in self.dialogue['quests']:
                    qd = self.dialogue['quests'][qid]
                    if quest.completed:
                        return qd.get('completed', self.dialogue.get('greeting', f"{self.name} 看着你，没有说话。"))
                    else:
                        return qd.get('active', self.dialogue.get('greeting', f"{self.name} 看着你，没有说话。"))
        return self.dialogue.get('greeting', f"{self.name} 看着你，没有说话。")

    def take_damage(self, amount):
        actual = max(1, amount - self.defense)
        self.hp -= actual
        return actual

    def get_total_defense(self):
        return self.defense

    def get_total_attack(self):
        return self.attack

NPCS = _load_npcs()

class Room:
    def __init__(self, room_id, data):
        self.id = room_id
        self.name = data['name']
        self.description = data['description']
        self.exits = data.get('exits', {})
        self.items = list(data.get('items', []))
        self.npcs = []
        for npc_id in data.get('npcs', []):
            if npc_id in NPCS:
                self.npcs.append(NPC(npc_id, NPCS[npc_id]))

    def describe(self, item_manager):
        lines = [f"\n【{self.name}】", self.description, ""]

        if self.items:
            item_names = [item_manager.get_name(iid) for iid in self.items]
            lines.append(f"地上的物品: {', '.join(item_names)}")

        if self.npcs:
            for npc in self.npcs:
                if npc.alive:
                    lines.append(f"[NPC] {npc.name}: {npc.description}")

        if self.exits:
            exit_desc = ", ".join([f"{dir_cn(k)}({k})" for k in self.exits.keys()])
            lines.append(f"\n出口: {exit_desc}")

        return "\n".join(lines)

    def get_npc(self, name):
        q = name.lower()
        for npc in self.npcs:
            if npc.alive and (q in npc.name.lower() or q in npc.id.lower()):
                return npc
        return None

    def remove_npc(self, npc):
        """Mark NPC dead (called after combat)."""
        npc.alive = False

    def extract_npc(self, npc):
        """Physically remove NPC from this room (used by patrol movement)."""
        if npc in self.npcs:
            self.npcs.remove(npc)

    def add_npc(self, npc):
        """Physically place NPC into this room (used by patrol movement)."""
        if npc not in self.npcs:
            self.npcs.append(npc)

def dir_cn(direction):
    mapping = {
        'north': '北', 'south': '南', 'east': '东', 'west': '西',
        'up': '上', 'down': '下'
    }
    return mapping.get(direction, direction)

class World:
    def __init__(self):
        self.item_manager = ItemManager()
        with open(os.path.join(DATA_DIR, 'rooms.json'), 'r', encoding='utf-8') as f:
            rooms_data = json.load(f)
        self.rooms = {rid: Room(rid, data) for rid, data in rooms_data.items()}

        # Build patrol registry: collect all patrolling NPC instances
        # and initialise their current_room_id to the room they're in.
        self._patrol_npcs = []
        for rid, room in self.rooms.items():
            for npc in room.npcs:
                if npc.patrol:
                    npc.current_room_id = rid   # override with actual placement
                    self._patrol_npcs.append(npc)

    def get_room(self, room_id):
        return self.rooms.get(room_id)

    def advance_patrols(self, now):
        """Advance any patrol NPC whose interval has elapsed.

        Returns list of (npc, old_room_id, new_room_id) for notifications.
        Called lazily from cmd_look / cmd_go — no separate thread needed.
        """
        moved = []
        for npc in self._patrol_npcs:
            if not npc.alive:
                continue
            if not npc.patrol:
                continue
            if now - npc.last_move_at < npc.patrol_interval:
                continue

            old_room_id = npc.current_room_id
            # Advance to the next waypoint
            npc.patrol_index = (npc.patrol_index + 1) % len(npc.patrol)
            new_room_id = npc.patrol[npc.patrol_index]

            if new_room_id == old_room_id:
                npc.last_move_at = now
                continue   # same room, no visible movement

            old_room = self.rooms.get(old_room_id)
            new_room = self.rooms.get(new_room_id)
            if not new_room:
                continue

            if old_room:
                old_room.extract_npc(npc)
            new_room.add_npc(npc)
            npc.current_room_id = new_room_id
            npc.last_move_at = now
            moved.append((npc, old_room_id, new_room_id))
        return moved
