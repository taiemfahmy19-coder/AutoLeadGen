import sqlite3, os

db_path = r'd:\AI feed\AutoLeadGen\data\leads.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Duplicate phones
c.execute("SELECT phone, COUNT(*) as cnt FROM leads WHERE phone IS NOT NULL AND phone != '' GROUP BY phone HAVING cnt > 1")
dups = c.fetchall()
print(f'Duplicate phones: {len(dups)} | examples: {dups[:5]}')

# Sample leads
c.execute("SELECT id, business_name, phone, status, score, whatsapp_status, source, city FROM leads ORDER BY id DESC LIMIT 15")
rows = c.fetchall()
print(f'\nAll {19} leads (recent first):')
for r in rows:
    nm = (r[1] or '')[:30]
    print(f'  id={r[0]:<4} name={nm:<32} phone={r[2]:<18} status={r[3]:<15} score={r[4]:<4} wa={r[5]:<12} src={r[6]} city={r[7]}')

# Merge history stats
c.execute("SELECT COUNT(*), COUNT(DISTINCT lead_id) FROM merge_history")
mh = c.fetchone()
print(f'\nMerge history: {mh[0]} records, {mh[1]} distinct lead_ids (with only 19 leads, this is ANOMALOUS)')

# Interactions
c.execute("SELECT id, lead_id, date, channel, status FROM interactions ORDER BY id")
ints = c.fetchall()
print(f'\nInteractions ({len(ints)}):')
for i in ints:
    print(f'  {i}')

# Searches
c.execute("SELECT * FROM searches")
searches = c.fetchall()
print(f'\nSearches: {searches}')

# Settings
c.execute("SELECT * FROM settings")
settings = c.fetchall()
print(f'Settings: {settings}')

# Audit log - action summary
c.execute("SELECT action, COUNT(*) as cnt FROM audit_log GROUP BY action ORDER BY cnt DESC")
audit_summary = c.fetchall()
print(f'\nAudit log action summary (2659 total):')
for a in audit_summary:
    print(f'  {a[0]}: {a[1]}')

# Check for orphaned merge_history (lead_id that no longer exists)
c.execute("SELECT COUNT(*) FROM merge_history WHERE lead_id NOT IN (SELECT id FROM leads)")
orphans = c.fetchone()[0]
print(f'\nOrphaned merge_history entries (lead_id missing from leads): {orphans}')

# Last 5 audit entries
c.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 5")
print(f'\nLast 5 audit log entries:')
for a in c.fetchall():
    print(f'  {a}')

conn.close()
