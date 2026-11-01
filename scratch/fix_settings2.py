import sys, ast, codecs
sys.path.insert(0, r'd:\AI feed\AutoLeadGen')

path = r'd:\AI feed\AutoLeadGen\ui\views\settings_view.py'

# Read with utf-8-sig to strip BOM
content = open(path, encoding='utf-8-sig', errors='replace').read()

# Fix the escaped quote if still present
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'فشلت' in line and 'res.get' in line:
        lines[i] = "                st.error(f\"فشلت: {res.get('error')}\")"
        print(f'Fixed L{i+1}')

# Write back without BOM
content_fixed = '\n'.join(lines)
with open(path, 'w', encoding='utf-8', newline='') as f:
    f.write(content_fixed)

# Verify
try:
    src = open(path, encoding='utf-8').read()
    ast.parse(src)
    print('settings_view.py: SYNTAX OK')
except SyntaxError as e:
    print(f'Error: {e}')
    lines2 = src.split('\n')
    ln = e.lineno or 1
    for j in range(max(0, ln-3), min(len(lines2), ln+3)):
        print(f'  L{j+1}: {repr(lines2[j])}')
