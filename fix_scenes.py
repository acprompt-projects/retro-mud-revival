import sys

with open('engine/ascii_renderer.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
new_lines = []
in_scenes = False
for line in lines:
    stripped = line.strip()
    if stripped == 'SCENES = {':
        in_scenes = True
    if stripped.startswith('}') and in_scenes:
        in_scenes = False
    
    # Match lines like: "        "#.............#",
    if in_scenes and stripped.startswith('"') and (stripped.endswith('"') or stripped.endswith('",')):
        has_comma = stripped.endswith('",')
        text = stripped[1:-2] if has_comma else stripped[1:-1]
        if len(text) != 40:
            if len(text) < 40:
                text = text.ljust(40)
            else:
                text = text[:40]
            indent = len(line) - len(line.lstrip())
            suffix = '",' if has_comma else '"'
            line = ' ' * indent + '"' + text + suffix
    new_lines.append(line)

content = '\n'.join(new_lines)
with open('engine/ascii_renderer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed all scene line lengths v2')
