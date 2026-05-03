import random
from .world import World
from .items import ItemManager

# Static scene templates for each room
# Width: 40 chars content, framed in 44-char border
# Special markers: @=player_spawn &=NPC_slot !=item_slot
SCENES = {
    "village_square": [
        "########################################",
        "#T...........T............T...........T#",
        "#......................................#",
        "#................@.....................#",
        "#...............==[]==.................#",
        "#...............|    |.................#",
        "#...............| ~~ |.................#",
        "#...............|    |.................#",
        "#T...........T............T...........T#",
        "########################################",
    ],
    "blacksmith": [
        "########################################",
        "#======= [BLACKSMITH] =========#        ",
        "#  [====]  ~~~  [====]                # ",
        "#  |    |  ~~~  |    |  &Wang         # ",
        "#  [====]  ~~~  [====]                # ",
        "#      ...........................    # ",
        "#      ...........................    # ",
        "#  [A] .................... [R]       # ",
        "#=======          ============== #      ",
        "########################################",
    ],
    "tavern": [
        "########################################",
        "#~~~~~~~~ [TAVERN] ~~~~~~~~#            ",
        "#~  TBL  TBL  TBL  TBL    ~#            ",
        "#~  CH   CH   CH   CH     ~#            ",
        "#~                        ~#            ",
        "#~      [BAR]   &Boss       ~#          ",
        "#~       BW  GL            ~#           ",
        "#~  FIRE                   ~#           ",
        "#~~~~~~~~       ~~~~~~~~#               ",
        "########################################",
    ],
    "forest_edge": [
        "########################################",
        "#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#",
        "#T......................T.............T#",
        "#T..........@.....................&...T#",
        "#T....................................T#",
        "#T..............PATH..................T#",
        "#T....................................T#",
        "#T......................T.............T#",
        "#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#",
        "########################################",
    ],
    "deep_path": [
        "########################################",
        "#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#",
        "#T.......T...................T.........T",
        "#T.......T.....@.............T.........T",
        "#T.......T...................T.........T",
        "#T.......T.....PATH..........T.........T",
        "#T.......T...................T.........T",
        "#T.......T...................T.........T",
        "#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#",
        "########################################",
    ],
    "ruins_entrance": [
        "########################################",
        "#^^^^^^^^^^^^ [RUINS] ^^^^^^^^^^^^^^^^# ",
        "#^  |    |    |    |    |    |       ^# ",
        "#^  |COL |    |COL |    |COL |  &Sk   ^#",
        "#^  |    |    |    |    |    |       ^# ",
        "#^....................................^#",
        "#^...........@........................^#",
        "#^....................................^#",
        "#^^^^^^^^^^^^ [=DUNGEON=] ^^^^^^^^^^^^# ",
        "########################################",
    ],
    "lakeside_camp": [
        "########################################",
        "#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#",
        "#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#",
        "#~~~~~~~ [LAKE CAMP] ~~~~~~~~~~~#       ",
        "#~~~~~~ [T] [FIRE] [T] ~~~~~~#          ",
        "#~~~~~~   &Mrc      .......... ~~~~~#   ",
        "#~~~~~~ ...........@.......... ~~~~~#   ",
        "#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#",
        "#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#",
        "########################################",
    ],
    "cave_entrance": [
        "########################################",
        "#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^#",
        "#^  DARK CAVE  ......................^# ",
        "#^  BONES BONES ....................^#  ",
        "#^  ...........@.............&Gob...^#  ",
        "#^  CLAW CLAW ......................^#  ",
        "#^  ................................^#  ",
        "#^  ................................^#  ",
        "#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^#",
        "########################################",
    ],
    "dungeon_1": [
        "########################################",
        "#[][][][][][][][][][][][][][][][][][][]#",
        "#[]  DUNGEON L1  ..................[]#  ",
        "#[]  TORCH ...........@............[]#  ",
        "#[]  CHAIN .........................[]# ",
        "#[]  ................&Slime.........[]# ",
        "#[]  POTS .........................[]#  ",
        "#[]  ..............................[]#  ",
        "#[][][][][][][][][][][][][][][][][][][]#",
        "########################################",
    ],
    "dungeon_2": [
        "########################################",
        "#[][][][][][][][][][][][][][][][][][][]#",
        "#[]  DUNGEON L2  MURAL MURAL     []#    ",
        "#[]  ...........@..................[]#  ",
        "#[]  ................&D.Slime......[]#  ",
        "#[]  ................&Skel.W.......[]#  ",
        "#[]  [GATE]  .....................[]#   ",
        "#[]  ..............................[]#  ",
        "#[][][][][][][][][][][][][][][][][][][]#",
        "########################################",
    ],
    "dungeon_3": [
        "########################################",
        "#[][][][][][][][][][][][][][][][][][][]#",
        "#[]        DUNGEON L3 - THRONE     []#  ",
        "#[]                                []#  ",
        "#[]         [OBSIDIAN THRONE]      []#  ",
        "#[]             &SKEL.KING         []#  ",
        "#[]         ...........@.....      []#  ",
        "#[]                                []#  ",
        "#[][][][][][][][][][][][][][][][][][][]#",
        "########################################",
    ],
}

# Animation presets applied automatically based on template markers
WAVE_CHARS = ["~", "≈", "-"]
FIRE_CHARS = ["^", "v"]
DUNGEON_WALL_CHARS = ["█", "▓", "▒", "░"]
GATE_CHARS = ["[", "{"]

DEFAULT_SCENE = [
    "########################################",
    "#......................................#",
    "#......................................#",
    "#............@.........................#",
    "#......................................#",
    "#......................................#",
    "#......................................#",
    "#......................................#",
    "#......................................#",
    "########################################",
]


class ASCIIRenderer:
    def __init__(self, world: World):
        self.world = world
        self.item_manager = ItemManager()
    
    def render_room(self, room_id, player, frame=0, combat_pos=None):
        room = self.world.get_room(room_id)
        if not room:
            return ["[未知区域]"]
        
        template = SCENES.get(room_id, DEFAULT_SCENE)
        # Deep copy grid
        grid = [list(row) for row in template]
        
        # Apply automatic animations based on template markers
        for r in range(len(grid)):
            for c in range(len(grid[r])):
                ch = grid[r][c]
                if ch == '~':
                    # Water wave animation
                    idx = (frame // 3) % len(WAVE_CHARS)
                    grid[r][c] = WAVE_CHARS[idx]
                elif ch == '^':
                    # Fire animation
                    idx = (frame // 2) % len(FIRE_CHARS)
                    grid[r][c] = FIRE_CHARS[idx]
                elif ch == '[' and 'dungeon' in room_id:
                    # Dungeon gate flicker
                    idx = (frame // 3) % len(GATE_CHARS)
                    grid[r][c] = GATE_CHARS[idx]
                elif ch == ']' and 'dungeon' in room_id:
                    # Sync closing bracket with opening
                    idx = (frame // 3) % len(GATE_CHARS)
                    grid[r][c] = '}' if idx == 1 else ']'
                elif ch == '#' and 'dungeon' in room_id and r in [0, 9]:
                    # Dungeon ceiling/floor pulse
                    pulse = ['#', '▓', '▒', '░']
                    idx = (frame // 4) % len(pulse)
                    grid[r][c] = pulse[idx]
        
        # Place items from room data into ! slots
        item_slots = []
        for r, row in enumerate(grid):
            for c, ch in enumerate(row):
                if ch == '!':
                    item_slots.append((r, c))
        for i, item_id in enumerate(room.items):
            if i < len(item_slots):
                r, c = item_slots[i]
                grid[r][c] = '!'
        for i in range(len(room.items), len(item_slots)):
            r, c = item_slots[i]
            grid[r][c] = '.'
        
        # Place NPCs from room data into & slots
        npc_slots = []
        for r, row in enumerate(grid):
            for c, ch in enumerate(row):
                if ch == '&':
                    npc_slots.append((r, c))
        alive_npcs = [n for n in room.npcs if n.alive]
        for i, npc in enumerate(alive_npcs):
            if i < len(npc_slots):
                r, c = npc_slots[i]
                grid[r][c] = '&'
        for i in range(len(alive_npcs), len(npc_slots)):
            r, c = npc_slots[i]
            grid[r][c] = '.'
        
        # Place player at @ slot
        for r, row in enumerate(grid):
            for c, ch in enumerate(row):
                if ch == '@':
                    grid[r][c] = '@'
        
        # Combat flash effect
        if combat_pos:
            cx, cy = combat_pos
            if 0 <= cy < len(grid) and 0 <= cx < len(grid[cy]):
                flash_chars = ['*', '+', 'x', '*']
                fc = flash_chars[frame % len(flash_chars)]
                grid[cy][cx] = fc
        
        # Build output with border
        lines = []
        lines.append(f"╔{'═'*42}╗")
        lines.append(f"║  {room.name:^38}  ║")
        lines.append(f"╠{'═'*42}╣")
        for row in grid:
            content = ''.join(row)[:40]
            lines.append(f"║  {content:<38}  ║")
        lines.append(f"╠{'═'*42}╣")
        
        # Status bar
        hp_bar = self._make_bar(player.hp, player.max_hp, 16, '█', '░')
        exp_bar = self._make_bar(player.exp % 100, 100, 8, '▓', '░')
        status = f"HP:[{hp_bar}] {player.hp}/{player.max_hp} Lv{player.level} EXP:[{exp_bar}]"
        lines.append(f"║  {status:<38}  ║")
        
        exits_str = ','.join(room.exits.keys()) if room.exits else '无'
        loc = f"位置:{room_id[:10]:<10} 出口:{exits_str}"
        lines.append(f"║  {loc:<38}  ║")
        lines.append(f"╚{'═'*42}╝")
        
        # Legend
        lines.append("  @你 &敌人 !物品 ~水 ^火 T树 #墙 .地")
        
        return lines
    
    def _make_bar(self, current, maximum, width, fill, empty):
        if maximum <= 0:
            return empty * width
        filled = int(current / maximum * width)
        return fill * filled + empty * (width - filled)
    
    def render_frame_sequence(self, room_id, player, frames=4, combat_pos=None):
        return [self.render_room(room_id, player, f, combat_pos) for f in range(frames)]
    
    def render_as_string(self, room_id, player, frame=0, combat_pos=None):
        lines = self.render_room(room_id, player, frame, combat_pos)
        return '\n'.join(lines)
