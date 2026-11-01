import os, ast, json

base = r'd:\AI feed\AutoLeadGen'
py_files = []
for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.venv', 'data', 'scratch']]
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            rel = path[len(base)+1:]
            size = os.path.getsize(path)
            try:
                src = open(path, encoding='utf-8', errors='ignore').read()
                tree = ast.parse(src)
                funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                py_files.append({'file': rel, 'size': size, 'lines': src.count('\n'), 'funcs': len(funcs), 'classes': len(classes), 'func_names': funcs[:15]})
            except SyntaxError as e:
                py_files.append({'file': rel, 'size': size, 'lines': 0, 'funcs': -1, 'SYNTAX_ERROR': str(e)})

for p in sorted(py_files, key=lambda x: x['size'], reverse=True):
    err = p.get('SYNTAX_ERROR', '')
    fn = p.get('func_names', [])
    print(f"{p['file']:60s} {p['size']:7d}B  {p.get('lines',0):4d}L  {p.get('funcs',0):3d}f  {'SYNTAX_ERROR: '+err if err else str(fn[:5])}")
