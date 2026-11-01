import sys
import os
import traceback

sys.path.insert(0, "d:/AI feed/AutoLeadGen")

from integrations.whatsapp_playwright import WhatsAppMessenger
from database.repository import LeadRepository

db = LeadRepository()
messenger = WhatsAppMessenger(db=db)

test_item = [
    {
        "id": 1,
        "phone": "+201012345678",
        "name": "Test Place",
        "message": "Hello test"
    }
]

with open("d:/AI feed/AutoLeadGen/scratch/send_diag.log", "w", encoding="utf-8") as log_f:
    def prog(curr, total, name, success, note):
        log_f.write(f"PROG: curr={curr} total={total} name={name} success={success} note={note}\n")
        log_f.flush()

    try:
        res = messenger.send_batch_automated(test_item, min_delay=1, max_delay=2, enable_human_typing=False, progress_callback=prog)
        log_f.write(f"RESULT: {res}\n")
    except Exception as e:
        log_f.write(f"EXCEPTION: {e}\n")
        log_f.write(traceback.format_exc())
