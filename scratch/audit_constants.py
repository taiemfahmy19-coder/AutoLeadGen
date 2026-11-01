import sys, os
sys.path.insert(0, r'd:\AI feed\AutoLeadGen')

src = open(r'd:\AI feed\AutoLeadGen\config\constants.py', encoding='utf-8', errors='ignore').read()

checks = ['HIGH_FIT_AI_INDUSTRIES', 'ALL_PRIORITIES', 'PRIORITY_HIGH', 'PRIORITY_MEDIUM', 'PRIORITY_LOW',
          'STATUS_FOLLOW_UP', 'STATUS_CONVERTED', 'STATUS_REJECTED',
          'DEFAULT_ARABIC_TEMPLATE', 'DEFAULT_ENGLISH_TEMPLATE',
          'WORLD_COUNTRIES_DATA', 'detect_country_and_language', 'MULTILINGUAL_TEMPLATES',
          'ARAB_COUNTRIES', 'WHATSAPP_BATCH_SIZE', 'WHATSAPP_COOLDOWN_MIN']
for c in checks:
    present = c in src
    status = 'YES' if present else 'NO'
    print(f'{status:3s} {c}')

print('\nData files:')
for root, dirs, files in os.walk(r'd:\AI feed\AutoLeadGen\data'):
    for f in files:
        path = os.path.join(root, f)
        size = os.path.getsize(path)
        rel = path[len(r'd:\AI feed\AutoLeadGen\data')+1:]
        print(f'  {rel:<45s} {size:>10,} bytes')

print('\nLogs:')
log_dir = r'd:\AI feed\AutoLeadGen\logs'
if os.path.exists(log_dir):
    for f in os.listdir(log_dir):
        path = os.path.join(log_dir, f)
        size = os.path.getsize(path)
        print(f'  {f:<30s} {size:>10,} bytes')
        # Show last 5 lines if .log
        if f.endswith('.log') and size > 0:
            try:
                lines = open(path, encoding='utf-8', errors='ignore').readlines()
                for ln in lines[-5:]:
                    print(f'    > {ln.rstrip()}')
            except:
                pass
else:
    print('  logs/ dir not found')
