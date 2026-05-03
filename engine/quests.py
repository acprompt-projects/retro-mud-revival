class Quest:
    def __init__(self, qid, data):
        self.id = qid
        self.name = data['name']
        self.description = data['description']
        # kill, collect, talk, fetch, escort
        self.type = data.get('type', 'kill')
        self.target = data.get('target', '')
        self.target_count = data.get('target_count', 1)
        self.original_count = data.get('target_count', 1)
        self.reward_exp = data.get('reward_exp', 10)
        self.reward_items = data.get('reward_items', [])
        self.reward_gold = data.get('reward_gold', 0)
        self.giver = data.get('giver', '')
        self.next_quest = data.get('next_quest', None)
        # fetch / escort
        self.deliver_to = data.get('deliver_to', '')
        self.destination = data.get('destination', '')
        self.escort_npc = data.get('escort_npc', '')
        # Hidden quests are not offered until trigger fires.
        # trigger schema: {"type": "has_item"|"completed_quest"|"level"|"in_room", "value": <str|int>}
        self.visible = data.get('visible', True)
        self.trigger = data.get('trigger', None)
        self.completed = False
        self.turned_in = False

    def progress_text(self):
        if self.completed:
            return "(已完成，可交任务)"
        done = self.original_count - self.target_count
        if self.type == 'kill':
            return f"(进度: 击杀 {done}/{self.original_count})"
        if self.type == 'collect':
            return f"(进度: 收集 {done}/{self.original_count})"
        if self.type == 'talk':
            return f"(进度: 找 {self.target} 谈话)"
        if self.type == 'fetch':
            return f"(进度: 把 {self.target} 交给 {self.deliver_to})"
        if self.type == 'escort':
            return f"(进度: 护送 {self.escort_npc} 到 {self.destination})"
        return f"(进度: {done}/{self.original_count})"


def _trigger_satisfied(player, trigger):
    """Used by hidden quest discovery."""
    if not trigger:
        return False
    t = trigger.get('type')
    v = trigger.get('value')
    if t == 'has_item':
        return v in player.inventory
    if t == 'completed_quest':
        return v in player.quest_log.completed
    if t == 'level':
        try:
            return player.level >= int(v)
        except (TypeError, ValueError):
            return False
    if t == 'in_room':
        return player.room_id == v
    return False

QUESTS = {
    "kill_wolf": {
        "name": "森林的威胁",
        "description": "村外的野狼最近频繁袭击路人，铁匠老王希望你能消灭那只野狼。",
        "type": "kill",
        "target": "wild_wolf",
        "target_count": 1,
        "reward_exp": 50,
        "reward_gold": 15,
        "reward_items": ["rusty_sword"],
        "giver": "blacksmith_wang",
        "next_quest": "kill_skeleton"
    },
    "kill_skeleton": {
        "name": "古遗迹的守卫",
        "description": "老王说他年轻时丢了一把剑在古遗迹里，但那里有骷髅战士看守。先把它解决掉。",
        "type": "kill",
        "target": "skeleton_warrior",
        "target_count": 1,
        "reward_exp": 120,
        "reward_gold": 40,
        "reward_items": ["steel_sword"],
        "giver": "blacksmith_wang"
    },
    "collect_potion": {
        "name": "采集药水",
        "description": "酒馆老板需要一些红色药水来招待冒险者。去村子里找找看。",
        "type": "collect",
        "target": "healing_potion",
        "target_count": 2,
        "reward_exp": 30,
        "reward_gold": 10,
        "reward_items": ["bread"],
        "giver": "tavern_boss",
        "next_quest": "explore_cave"
    },
    "explore_cave": {
        "name": "洞穴调查",
        "description": "有人看到地精侦察兵在黑暗洞穴附近出没（森林边缘往西）。去看看情况，把那家伙解决了再回来报告。",
        "type": "kill",
        "target": "goblin_scout",
        "target_count": 1,
        "reward_exp": 100,
        "reward_gold": 25,
        "reward_items": ["healing_potion", "healing_potion"],
        "giver": "tavern_boss"
    },
    "talk_merchant": {
        "name": "湖边的商人",
        "description": "酒馆老板听说有个旅行商人在湖边扎营，想知道他卖些什么。去湖边营地找他聊聊。",
        "type": "talk",
        "target": "traveling_merchant",
        "target_count": 1,
        "reward_exp": 20,
        "reward_gold": 20,
        "reward_items": [],
        "giver": "tavern_boss"
    },
    "fetch_crown": {
        "name": "白骨王冠的归宿",
        "description": "铁匠老王听说地牢深处有件骨制的王冠，想看看那种古代工艺。如果你拿到了，把它带给老王。",
        "type": "fetch",
        "target": "crown_of_bones",
        "target_count": 1,
        "deliver_to": "blacksmith_wang",
        "reward_exp": 200,
        "reward_gold": 100,
        "reward_items": ["steel_sword"],
        "giver": "blacksmith_wang"
    },
    "escort_merchant": {
        "name": "护送旅行商人",
        "description": "旅行商人想去铁匠铺补货，但森林路上不太平。护送他从湖边营地一路到铁匠铺。",
        "type": "escort",
        "escort_npc": "traveling_merchant",
        "destination": "blacksmith",
        "target_count": 1,
        "reward_exp": 80,
        "reward_gold": 30,
        "reward_items": ["healing_potion"],
        "giver": "traveling_merchant"
    },
    "hidden_blacksmith_secret": {
        "name": "老王的秘密武器",
        "description": "你身上的白骨王冠引起了老王的注意。他凑过来低声说，他年轻时有把家传的青铜匕首被骷髅王夺走，藏在地牢三层。如果你能拿到，他愿意倾囊相授。",
        "type": "fetch",
        "target": "magic_dagger",
        "target_count": 1,
        "deliver_to": "blacksmith_wang",
        "reward_exp": 300,
        "reward_gold": 150,
        "reward_items": ["steel_sword", "healing_potion", "healing_potion"],
        "giver": "blacksmith_wang",
        "visible": False,
        "trigger": {"type": "has_item", "value": "crown_of_bones"}
    }
}

class QuestLog:
    def __init__(self):
        self.active = {}
        self.completed = []
    
    def assign(self, qid):
        if qid in QUESTS and qid not in self.active and qid not in self.completed:
            self.active[qid] = Quest(qid, QUESTS[qid])
            return self.active[qid]
        return None
    
    def check_kill(self, npc_id):
        updated = []
        for qid, quest in self.active.items():
            if quest.type == 'kill' and quest.target == npc_id:
                quest.target_count -= 1
                if quest.target_count <= 0:
                    quest.completed = True
                updated.append(quest.name)
        return updated
    
    def check_collect(self, item_id):
        updated = []
        for qid, quest in self.active.items():
            if quest.type == 'collect' and quest.target == item_id:
                quest.target_count -= 1
                if quest.target_count <= 0:
                    quest.completed = True
                updated.append(quest.name)
        return updated

    def check_talk(self, npc_id):
        updated = []
        for qid, quest in self.active.items():
            if quest.type == 'talk' and quest.target == npc_id and not quest.completed:
                quest.target_count -= 1
                if quest.target_count <= 0:
                    quest.completed = True
                updated.append(quest.name)
        return updated

    def turnable_to(self, npc_id):
        return [qid for qid, q in self.active.items()
                if q.completed and not q.turned_in and q.giver == npc_id]

    def check_fetch(self, player, npc_id):
        """Called when player talks to an NPC. If a fetch quest's deliver_to
        matches and the player has the target item, consume it and complete.
        Returns list of (quest_name, item_name) for the items consumed."""
        consumed = []
        for qid, quest in list(self.active.items()):
            if quest.type != 'fetch' or quest.completed:
                continue
            if quest.deliver_to != npc_id:
                continue
            if quest.target in player.inventory:
                player.remove_item(quest.target)
                quest.target_count -= 1
                if quest.target_count <= 0:
                    quest.completed = True
                consumed.append((quest.name, quest.target))
        return consumed

    def check_escort_arrival(self, player, room_id):
        """Called on cmd_go when entering a new room. Marks escort quests
        completed if their destination is reached."""
        arrived = []
        for qid, quest in self.active.items():
            if quest.type != 'escort' or quest.completed:
                continue
            if quest.destination == room_id:
                quest.completed = True
                arrived.append(quest.name)
        return arrived

    def discover_hidden(self, player, npc_id):
        """Reveal hidden quests offered by this NPC whose trigger now matches.
        Returns list of (qid, qdata) newly revealed (caller offers them)."""
        revealed = []
        for qid, qdata in QUESTS.items():
            if qdata.get('visible', True):
                continue
            if qdata.get('giver') != npc_id:
                continue
            if qid in self.active or qid in self.completed:
                continue
            if _trigger_satisfied(player, qdata.get('trigger')):
                revealed.append((qid, qdata))
        return revealed

    def active_escort_npc(self):
        """Return the npc_id currently being escorted (companion still in tow,
        until the quest is turned in)."""
        for q in self.active.values():
            if q.type == 'escort' and not q.turned_in:
                return q.escort_npc
        return None
    
    def can_turn_in(self, qid):
        quest = self.active.get(qid)
        return quest and quest.completed and not quest.turned_in
    
    def turn_in(self, qid):
        quest = self.active.pop(qid, None)
        if quest:
            quest.turned_in = True
            self.completed.append(qid)
            return quest
        return None
    
    def describe(self):
        lines = []
        if self.active:
            lines.append("【当前任务】")
            for qid, q in self.active.items():
                lines.append(f"  - [{qid}] {q.name}: {q.description} {q.progress_text()}")
        else:
            lines.append("当前没有进行中的任务。")
        if self.completed:
            lines.append(f"\n已完成任务数: {len(self.completed)}")
        return "\n".join(lines)
