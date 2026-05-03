import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def _load_loot_table():
    path = os.path.join(DATA_DIR, 'loot.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

_LOOT_TABLE = _load_loot_table()

def roll_loot(npc_id):
    """Return list of item_ids dropped by this NPC (may be empty)."""
    entries = _LOOT_TABLE.get(npc_id, [])
    drops = []
    for entry in entries:
        count = entry.get('count', 1)
        for _ in range(count):
            if random.random() < entry.get('chance', 0):
                drops.append(entry['item_id'])
    return drops


class CombatSystem:
    @staticmethod
    def fight_round(attacker, defender):
        """Return (attacker_hit, damage, defender_alive, message)"""
        damage = max(1, attacker.get_total_attack() - defender.get_total_defense())
        if hasattr(defender, 'take_damage'):
            actual = defender.take_damage(damage)
        else:
            actual = damage
            defender.hp -= damage

        msg = f"{attacker.name} 攻击 {defender.name}，造成 {actual} 点伤害！"
        alive = defender.hp > 0
        if not alive:
            msg += f" {defender.name} 倒下了！"
        else:
            msg += f" ({defender.name} 剩余 {defender.hp}/{defender.max_hp} HP)"

        return True, actual, alive, msg

    @staticmethod
    def player_attack_npc(player, npc, world):
        msgs = []
        # Player attacks
        hit, dmg, alive, msg = CombatSystem.fight_round(player, npc)
        msgs.append(msg)

        if not alive:
            room = world.get_room(player.room_id)
            room.remove_npc(npc)
            msgs.append(f"你击败了 {npc.name}！")

            # EXP reward
            exp_gain = npc.max_hp // 5
            player.add_exp(exp_gain)
            msgs.append(f"获得 {exp_gain} 点经验！")

            # Loot drops
            drops = roll_loot(npc.id)
            if drops:
                from .items import ItemManager
                im = ItemManager()
                for item_id in drops:
                    room.items.append(item_id)
                    msgs.append(f"[掉落] {npc.name} 掉落了 {im.get_name(item_id)}（已放置在地上）。")

            # Check quests
            quest_updates = player.quest_log.check_kill(npc.id)
            for qu in quest_updates:
                msgs.append(f"[任务更新] {qu}")

            player.in_combat = False
            player.combat_target = None
            return msgs

        # NPC counter-attacks
        hit2, dmg2, player_alive, msg2 = CombatSystem.fight_round(npc, player)
        msgs.append(msg2)

        if not player_alive:
            msgs.append("你眼前一黑，失去了意识...")
            msgs.append("（你在村庄广场醒来，生命值恢复到 20）")
            player.hp = 20
            player.room_id = "village_square"
            player.in_combat = False
            player.combat_target = None

        return msgs
