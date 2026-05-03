import time
from .world import World
from .items import ItemManager
from .combat import CombatSystem
from .merchant import SHOPS
from .save import SaveManager
from .ascii_renderer import ASCIIRenderer

class CommandProcessor:
    def __init__(self, world: World, players: dict):
        self.world = world
        self.players = players
        self.item_manager = ItemManager()
        self.ascii_renderer = ASCIIRenderer(world)

    # ------------------------------------------------------------------
    # Patrol helper — call before any action that can show room contents
    # ------------------------------------------------------------------
    def _tick_patrols(self):
        """Advance patrol NPCs and notify players in affected rooms."""
        moved = self.world.advance_patrols(time.time())
        for npc, old_rid, new_rid in moved:
            for p in self.players.values():
                if p.room_id == old_rid:
                    p.send(f"[巡逻] {npc.name} 离开了这里。")
                elif p.room_id == new_rid:
                    p.send(f"[巡逻] {npc.name} 巡逻至此。")

    # ------------------------------------------------------------------
    # Command dispatch
    # ------------------------------------------------------------------
    def process(self, player, raw_cmd):
        parts = raw_cmd.strip().split()
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        arg_str = ' '.join(args)

        handler = getattr(self, f'cmd_{cmd}', None)
        if handler:
            handler(player, args, arg_str)
        else:
            # Try alias
            aliases = {
                'l': 'look', 'i': 'inventory', 'inv': 'inventory',
                'get': 'take', 'move': 'go', 'kill': 'attack',
                'h': 'help', '?': 'help'
            }
            if cmd in aliases:
                real = aliases[cmd]
                handler = getattr(self, f'cmd_{real}', None)
                if handler:
                    handler(player, args, arg_str)
                    return
            player.send(f"未知命令: '{cmd}'。输入 help 查看可用命令。")

    def cmd_look(self, player, args, arg_str):
        self._tick_patrols()
        ascii_text = self.ascii_renderer.render_as_string(player.room_id, player, frame=0)
        player.send(ascii_text)

        # Show other players in the same room
        others = [p for p in self.players.values() if p != player and p.room_id == player.room_id]
        if others:
            names = ', '.join([p.name for p in others])
            player.send(f"\n[玩家] 你也看到了: {names}")

        # Show active escort companion
        escort_id = player.quest_log.active_escort_npc()
        if escort_id:
            from .world import NPCS
            ename = NPCS.get(escort_id, {}).get('name', escort_id)
            player.send(f"[同行] {ename} 紧跟在你身边。")

    def cmd_go(self, player, args, arg_str):
        if not args:
            player.send("你要往哪个方向走？")
            return
        direction = args[0].lower()
        room = self.world.get_room(player.room_id)
        if direction not in room.exits:
            player.send(f"那边没有路。可用出口: {', '.join(room.exits.keys())}")
            return

        if player.in_combat:
            player.send("你正在战斗中，无法逃跑！")
            return

        self._tick_patrols()

        old_room = player.room_id
        player.room_id = room.exits[direction]
        new_room = self.world.get_room(player.room_id)
        player.send(f"你向 {direction} 走去...")
        player.send(new_room.describe(self.item_manager))

        # Escort: companion follows
        escort_id = player.quest_log.active_escort_npc()
        if escort_id:
            from .world import NPCS
            ename = NPCS.get(escort_id, {}).get('name', escort_id)
            player.send(f"[同行] {ename} 跟着你过来了。")

        # Escort: arrival check
        arrived = player.quest_log.check_escort_arrival(player, player.room_id)
        for qname in arrived:
            player.send(f"[任务更新] {qname}: 你成功护送目标到达终点！可向委托人复命。")

        # Notify others in old room
        for p in self.players.values():
            if p != player and p.room_id == old_room:
                p.send(f"{player.name} 向 {direction} 离开了。")

        # Notify others in new room
        for p in self.players.values():
            if p != player and p.room_id == player.room_id:
                p.send(f"{player.name} 走了过来。")

    def cmd_take(self, player, args, arg_str):
        if not args:
            player.send("你要拿什么？")
            return
        room = self.world.get_room(player.room_id)
        target = arg_str.lower()

        found = None
        for iid in room.items:
            item = self.item_manager.get(iid)
            if item and (target in item['name'].lower() or target in iid.lower()):
                found = iid
                break

        if not found:
            player.send("这里没有那个物品。")
            return

        room.items.remove(found)
        player.add_item(found)
        player.send(f"你捡起了 {self.item_manager.get_name(found)}。")

        # Collect-type quest progress
        collect_updates = player.quest_log.check_collect(found)
        for cu in collect_updates:
            player.send(f"[任务更新] {cu}: 物品已收集，可向委托人复命。")

    def cmd_drop(self, player, args, arg_str):
        if not args:
            player.send("你要丢什么？")
            return
        target = arg_str.lower()
        found = None
        for iid in player.inventory:
            item = self.item_manager.get(iid)
            if item and (target in item['name'].lower() or target in iid.lower()):
                found = iid
                break

        if not found:
            player.send("你身上没有那个物品。")
            return

        player.remove_item(found)   # remove_item now auto-unequips from dict
        room = self.world.get_room(player.room_id)
        room.items.append(found)
        player.send(f"你丢下了 {self.item_manager.get_name(found)}。")

    def cmd_inventory(self, player, args, arg_str):
        player.send(player.get_inventory_desc(self.item_manager))

    def cmd_use(self, player, args, arg_str):
        if not args:
            player.send("你要使用什么？")
            return
        target = arg_str.lower()
        found = None
        for iid in player.inventory:
            item = self.item_manager.get(iid)
            if item and (target in item['name'].lower() or target in iid.lower()):
                found = iid
                break

        if not found:
            player.send("你身上没有那个物品。")
            return

        item = self.item_manager.get(found)
        if not item.get('usable'):
            player.send(f"{item['name']} 无法直接使用。")
            return

        if item.get('type') == 'consumable' and 'heal_amount' in item:
            healed = player.heal(item['heal_amount'])
            player.remove_item(found)
            player.send(f"你使用了 {item['name']}，恢复了 {healed} 点生命。 (HP: {player.hp}/{player.max_hp})")

    def cmd_equip(self, player, args, arg_str):
        if not args:
            player.send("你要装备什么？")
            return
        target = arg_str.lower()
        found = None
        for iid in player.inventory:
            item = self.item_manager.get(iid)
            if item and (target in item['name'].lower() or target in iid.lower()):
                found = iid
                break

        if not found:
            player.send("你身上没有那个物品。")
            return

        item = self.item_manager.get(found)
        slot = item.get('slot')
        if not slot or slot not in player.equipped:
            player.send(f"{item['name']} 没有可用的装备栏位（该物品无法装备）。")
            return

        # Unequip old item in the same slot (stays in inventory)
        old = player.equipped.get(slot)
        if old:
            old_name = self.item_manager.get_name(old)
            player.send(f"你卸下了 {old_name}。")

        player.equipped[slot] = found
        slot_label = player._SLOT_LABEL.get(slot, slot)
        player.send(f"你装备了 {item['name']}（{slot_label}槽）。")
        player.send(f"当前攻击: {player.get_total_attack()} | 当前防御: {player.get_total_defense()}")

    def cmd_unequip(self, player, args, arg_str):
        if not args:
            player.send("请指定槽位名称: weapon / armor / shield / accessory")
            return
        slot = args[0].lower()
        if slot not in player.equipped:
            player.send(f"未知槽位 '{slot}'。可选: weapon, armor, shield, accessory")
            return
        eid = player.equipped.get(slot)
        if not eid:
            player.send(f"该槽位（{slot}）当前没有装备。")
            return
        ename = self.item_manager.get_name(eid)
        player.equipped[slot] = None
        player.send(f"你卸下了 {ename}（{slot} 槽已清空）。")

    def cmd_attack(self, player, args, arg_str):
        if not args:
            player.send("你要攻击谁？")
            return
        room = self.world.get_room(player.room_id)
        target = arg_str.lower()
        npc = room.get_npc(target)

        if not npc:
            player.send("这里没有那个目标。")
            return

        if not npc.hostile and not npc.alive:
            player.send("你无法攻击那个目标。")
            return

        player.in_combat = True
        player.combat_target = npc
        player.send(f"你向 {npc.name} 发起了攻击！")

        msgs = CombatSystem.player_attack_npc(player, npc, self.world)
        for m in msgs:
            player.send(m)

    def cmd_talk(self, player, args, arg_str):
        if not args:
            player.send("你要和谁说话？")
            return
        room = self.world.get_room(player.room_id)
        target = arg_str.lower()
        npc = room.get_npc(target)

        if not npc:
            player.send("这里没有那个人。")
            return

        if not npc.alive:
            player.send(f"{npc.name} 已经无法回应你了。")
            return

        player.send(f"【{npc.name}】")

        # Topic matching: if extra args beyond NPC name, try topic first
        topic = None
        if len(args) > 1:
            topic = args[1].lower()
        if topic and 'topics' in npc.dialogue and topic in npc.dialogue['topics']:
            player.send(npc.dialogue['topics'][topic])
        else:
            player.send(npc.get_greeting(player))
            if topic:
                player.send(f"（{npc.name} 对这个话题没有什么可说的。你可以试试: {', '.join(npc.dialogue.get('topics', {}).keys())}）")

        # Talk-type quest progress
        talk_updates = player.quest_log.check_talk(npc.id)
        for tu in talk_updates:
            player.send(f"[任务更新] {tu}: 你完成了与目标的对话！")

        # Fetch-type quest delivery
        fetched = player.quest_log.check_fetch(player, npc.id)
        for qname, item_id in fetched:
            iname = self.item_manager.get_name(item_id)
            player.send(f"[任务更新] {qname}: 你把 {iname} 交给了 {npc.name}。")

        # Turn in any completed quests where this NPC is the giver
        turnable = player.quest_log.turnable_to(npc.id)
        for qid in turnable:
            self._turn_in_quest(player, qid, npc)

        # Hidden quest discovery
        for qid, qdata in player.quest_log.discover_hidden(player, npc.id):
            player.send(f"\n[隐藏任务] {npc.name} 凑近你低声说: 『{qdata['name']}』 [ID: {qid}]")
            player.send(f"说明: {qdata['description']}")
            player.send(f"输入 'quest accept {qid}' 接受任务。")

        # Quest offer (visible quests only)
        from .quests import QUESTS
        for qid, qdata in QUESTS.items():
            if not qdata.get('visible', True):
                continue
            if qdata.get('giver') == npc.id and qid not in player.quest_log.active and qid not in player.quest_log.completed:
                player.send(f"\n[任务] {npc.name} 想要委托你: 『{qdata['name']}』 [ID: {qid}]")
                player.send(f"说明: {qdata['description']}")
                player.send(f"输入 'quest accept {qid}' 接受任务。")
                break

        # Shop
        if npc.id in SHOPS:
            shop = SHOPS[npc.id]
            player.send(f"\n{shop.list_goods(self.item_manager)}")
            player.send("输入 'buy <物品名>' 购买，'sell <物品名>' 出售。")

    def _turn_in_quest(self, player, qid, npc):
        from .quests import QUESTS
        quest = player.quest_log.active.get(qid)
        if not quest:
            return
        player.send(f"\n[任务交付] 你向 {npc.name} 复命：『{quest.name}』")
        # Rewards
        if quest.reward_exp:
            leveled, old_lv, new_lv = player.add_exp(quest.reward_exp)
            player.send(f"  + 获得 {quest.reward_exp} 点经验")
            if leveled:
                player.send(f"  ★ 升级！Lv {old_lv} → Lv {new_lv}（生命+20，攻击+2，防御+1）")
        if quest.reward_gold:
            player.gold += quest.reward_gold
            player.send(f"  + 获得 {quest.reward_gold} 铜币 (当前: {player.gold})")
        for iid in quest.reward_items:
            player.add_item(iid)
            player.send(f"  + 获得物品: {self.item_manager.get_name(iid)}")
        player.quest_log.turn_in(qid)
        # Chained follow-up
        if quest.next_quest and quest.next_quest in QUESTS:
            nq = QUESTS[quest.next_quest]
            player.send(f"\n[任务] {npc.name} 又有新的请求: 『{nq['name']}』 [ID: {quest.next_quest}]")
            player.send(f"说明: {nq['description']}")
            player.send(f"输入 'quest accept {quest.next_quest}' 接受任务。")

    def cmd_say(self, player, args, arg_str):
        if not arg_str:
            player.send("你要说什么？")
            return
        player.send(f"你说: {arg_str}")
        for p in self.players.values():
            if p != player and p.room_id == player.room_id:
                p.send(f"{player.name} 说: {arg_str}")

    def cmd_quest(self, player, args, arg_str):
        if args and args[0] == 'accept':
            qid = args[1] if len(args) > 1 else ''
            if not qid:
                player.send("请指定任务ID。例如: quest accept kill_wolf")
                return
            from .quests import QUESTS, _trigger_satisfied
            if qid not in QUESTS:
                player.send(f"没有这个任务: {qid}")
                return
            qd = QUESTS[qid]
            if not qd.get('visible', True) and not _trigger_satisfied(player, qd.get('trigger')):
                player.send("无法接受该任务（条件未达成）。")
                return
            if player.quest_log.assign(qid):
                quest = player.quest_log.active[qid]
                player.send(f"任务『{qd['name']}』已接受！输入 quest 查看进度。")
                if quest.type == 'escort':
                    from .world import NPCS
                    ename = NPCS.get(quest.escort_npc, {}).get('name', quest.escort_npc)
                    dest_room = self.world.get_room(quest.destination)
                    dest_name = dest_room.name if dest_room else quest.destination
                    player.send(f"[护送] {ename} 现在跟随你，目的地: {dest_name}。")
            else:
                player.send("无法接受该任务（可能已在进行中或已完成）。")
            return
        player.send(player.quest_log.describe())

    def cmd_buy(self, player, args, arg_str):
        if not args:
            player.send("你要买什么？")
            return
        room = self.world.get_room(player.room_id)
        target = arg_str.lower()

        shop_npc = None
        for npc in room.npcs:
            if npc.alive and npc.id in SHOPS:
                shop_npc = npc
                break

        if not shop_npc:
            player.send("这里没有商人。")
            return

        shop = SHOPS[shop_npc.id]
        found_id = None
        for iid in shop.inventory:
            item = self.item_manager.get(iid)
            if item and (target in item['name'].lower() or target in iid.lower()):
                found_id = iid
                break

        if not found_id:
            player.send("这里没有卖那个物品。")
            return

        price = shop.get_price(found_id)
        if player.gold < price:
            player.send(f"金币不足。需要 {price} 铜币，你只有 {player.gold}。")
            return

        player.gold -= price
        player.add_item(found_id)
        player.send(f"你花费 {price} 铜币购买了 {self.item_manager.get_name(found_id)}。剩余金币: {player.gold}")

    def cmd_sell(self, player, args, arg_str):
        if not args:
            player.send("你要卖什么？")
            return
        room = self.world.get_room(player.room_id)
        target = arg_str.lower()

        shop_npc = None
        for npc in room.npcs:
            if npc.alive and npc.id in SHOPS:
                shop_npc = npc
                break

        if not shop_npc:
            player.send("这里没有商人。")
            return

        found_id = None
        for iid in player.inventory:
            item = self.item_manager.get(iid)
            if item and (target in item['name'].lower() or target in iid.lower()):
                found_id = iid
                break

        if not found_id:
            player.send("你身上没有那个物品。")
            return

        price = max(1, SHOPS[shop_npc.id].get_price(found_id) // 2)
        player.remove_item(found_id)   # auto-unequips via remove_item
        player.gold += price
        player.send(f"你出售了 {self.item_manager.get_name(found_id)}，获得 {price} 铜币。当前金币: {player.gold}")

    def cmd_save(self, player, args, arg_str):
        sm = SaveManager()
        path = sm.save(player, self.world)
        player.send(f"游戏已存档: {path}")

    def cmd_load(self, player, args, arg_str):
        sm = SaveManager()
        data = sm.load(player.name, player, self.world)
        if data:
            player.send(f"存档已读取。欢迎回来，{player.name}！")
            room = self.world.get_room(player.room_id)
            player.send(room.describe(self.item_manager))
        else:
            player.send("没有找到存档。")

    def cmd_status(self, player, args, arg_str):
        player.send(player.get_status_desc())
        if player.in_combat:
            player.send("状态: 战斗中")
        # Active quests summary
        if player.quest_log.active:
            lines = ["\n【任务进度】"]
            for qid, q in player.quest_log.active.items():
                lines.append(f"  [{qid}] {q.name} {q.progress_text()}")
            player.send("\n".join(lines))

    def cmd_who(self, player, args, arg_str):
        if not self.players:
            player.send("当前没有在线玩家。")
            return
        lines = ["【在线玩家】"]
        for p in self.players.values():
            room = self.world.get_room(p.room_id)
            room_name = room.name if room else p.room_id
            lines.append(f"  {p.name} @ {room_name}")
        player.send("\n".join(lines))

    def cmd_help(self, player, args, arg_str):
        lines = [
            "【可用命令】",
            "  look / l           - 观察周围环境",
            "  go <方向>          - 移动 (north/south/east/west)",
            "  take <物品>        - 捡起物品",
            "  drop <物品>        - 丢弃物品",
            "  inventory / i      - 查看背包与装备",
            "  use <物品>         - 使用物品（药水、食物）",
            "  equip <物品>       - 装备武器/护甲/盾牌/饰品",
            "  unequip <槽位>     - 卸下装备 (weapon/armor/shield/accessory)",
            "  attack <目标>      - 攻击敌人",
            "  talk <NPC>         - 与 NPC 对话/接任务/交易",
            "  say <内容>         - 说话（同房间玩家可见）",
            "  quest              - 查看任务列表",
            "  quest accept <id>  - 接受任务",
            "  buy <物品>         - 从商人处购买",
            "  sell <物品>        - 向商人出售",
            "  who                - 查看在线玩家",
            "  save               - 存档",
            "  load               - 读档",
            "  status             - 查看自身状态",
            "  help / ?           - 显示本帮助",
            "  quit               - 退出游戏",
            ""
        ]
        player.send("\n".join(lines))

    def cmd_quit(self, player, args, arg_str):
        player.send("再见，冒险者！")
        if player.writer:
            player.writer.close()
