from pathlib import Path

path = Path('modules/tui.py')
lines = path.read_text(encoding='utf-8', errors='ignore').splitlines(keepends=True)
changed = False
for i, line in enumerate(lines):
    if 'id="delete"' in line and 'Kategorie' in line:
        lines[i] = line.replace('id="delete"', 'id="delete_category"')
        changed = True
        break
if changed:
    path.write_text(''.join(lines), encoding='utf-8')
    print('Patched category delete button id')
else:
    print('No matching line found to patch')
