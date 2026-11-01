import sys
sys.path.insert(0, r'd:\AI feed\AutoLeadGen')

# Quick fix: read the file and fix line 378 directly
path = r'd:\AI feed\AutoLeadGen\ui\views\settings_view.py'
content = open(path, encoding='utf-8', errors='replace').read()

# Replace the broken escaped quote pattern
bad  = r"""st.error(f"فشلت: {res.get(\'error\')}")"""
good = """st.error(f"فشلت: {res.get('error')}")"""

if bad in content:
    content = content.replace(bad, good)
    open(path, 'w', encoding='utf-8').write(content)
    print('FIXED the escaped quote')
else:
    # Try another pattern
    import re
    # Find the line
    lines = content.split('\n')
    fixed = False
    for i, line in enumerate(lines):
        if 'فشلت' in line and 'res.get' in line:
            lines[i] = "                st.error(f\"فشلت: {res.get('error')}\")"
            fixed = True
            print(f'Fixed line {i+1}: {lines[i].strip()}')
    if fixed:
        open(path, 'w', encoding='utf-8').write('\n'.join(lines))
    else:
        print('Pattern not found, showing the line:')
        for i, line in enumerate(lines):
            if 'فشلت' in line:
                print(f'L{i+1}: {repr(line)}')

# Verify
import ast
try:
    src = open(path, encoding='utf-8', errors='replace').read()
    ast.parse(src)
    print('settings_view.py: SYNTAX OK')
except SyntaxError as e:
    print(f'Still broken: {e}')
