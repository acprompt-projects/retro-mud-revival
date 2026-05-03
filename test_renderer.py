import sys, os, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix stdout encoding on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from engine.world import World
from engine.player import Player
from engine.ascii_renderer import ASCIIRenderer

world = World()
player = Player("TestHero", None)
renderer = ASCIIRenderer(world)

lines = []

# Test render a few rooms
for room_id in ["village_square", "forest_edge", "dungeon_3"]:
    lines.append(f"\n{'='*50}")
    lines.append(f"ROOM: {room_id}")
    lines.append(f"{'='*50}")
    player.room_id = room_id
    text = renderer.render_as_string(room_id, player, frame=0)
    lines.append(text)

# Test animation frames
lines.append(f"\n{'='*50}")
lines.append("ANIMATION FRAMES (dungeon_3)")
lines.append(f"{'='*50}")
player.room_id = "dungeon_3"
frames = renderer.render_frame_sequence("dungeon_3", player, frames=4)
for i, frame in enumerate(frames):
    lines.append(f"\n--- Frame {i} ---")
    lines.append('\n'.join(frame[:9]))

output = '\n'.join(lines)
with open('test_renderer_output.txt', 'w', encoding='utf-8') as f:
    f.write(output)

print('Renderer test complete. See test_renderer_output.txt')
