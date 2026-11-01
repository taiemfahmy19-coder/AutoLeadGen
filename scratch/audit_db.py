import sqlite3, os

db_path = r'd:\AI feed\AutoLeadGen\data\leads.db'
if not os.path.exists(db_path):
    print('DB not found at', db_path)
else:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in c.fetchall()]
    print('TABLES:', tables)
    for t in tables:
        c.execute(f'SELECT COUNT(*) FROM "{t}"')
        cnt = c.fetchone()[0]
        c.execute(f'PRAGMA table_info("{t}")')
        cols = [r[1] for r in c.fetchall()]
        print(f'  {t}: {cnt} rows | cols: {cols}')
    c.execute('PRAGMA integrity_check')
    print('INTEGRITY:', c.fetchone()[0])
    c.execute('PRAGMA wal_mode')
    print('WAL mode:', c.fetchone()[0])
    c.execute('PRAGMA foreign_keys')
    print('Foreign keys pragma:', c.fetchone()[0])
    
    # Check for duplicate phones
    c.execute("SELECT phone, COUNT(*) as cnt FROM leads WHERE phone IS NOT NULL AND phone != '' GROUP BY phone HAVING cnt > 1")
    dups = c.fetchall()
    print(f'Duplicate phones: {len(dups)}')
    
    # Sample leads
    c.execute("SELECT id, business_name, phone, status, score, whatsapp_status, source, city FROM leads ORDER BY id DESC LIMIT 10")
    rows = c.fetchall()
    print(f'\nRecent leads sample ({len(rows)} shown):')
    for r in rows:
        print(f'  id={r[0]} name={r[1][:25]} phone={r[2]} status={r[3]} score={r[4]} wa={r[5]} src={r[6]} city={r[7]}')
    
    # Audit log sample
    c.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 5")
    audit = c.fetchall()
    print(f'\nAudit log (last 5):')
    for a in audit:
        print(f'  {a}')
    
    conn.close()
