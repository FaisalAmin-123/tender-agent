# api_worker.py
import os
import sys
import argparse
import time

sys.path.insert(0, os.path.dirname(__file__))

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--num", type=int, default=int(os.getenv("MAX_PDFS", "10")))
    p.add_argument("--group", type=str, default=os.getenv("WHATSAPP_GROUP_NAME"))
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    os.environ['MAX_PDFS'] = str(args.num)
    print(f"[worker] Starting: num={args.num}, group={args.group}")
    try:
        import main
        import whatsapp_group_sender
        # 1) run the scraper (this should download PDFs to DOWNLOAD_DIR)
        try:
            main.main()
        except Exception as e:
            print("[worker] Error running main.main():", e)

        # 2) send to whatsapp if group provided
        if args.group:
            try:
                sent = whatsapp_group_sender.send_files_to_group(args.group, max_files=args.num)
                print("[worker] WhatsApp send result:", sent)
            except Exception as e:
                print("[worker] Error sending to WhatsApp:", e)
        else:
            print("[worker] No whatsapp group specified; skipping WhatsApp send.")
    except Exception as ex:
        print("[worker] Worker failed to import modules or run job:", ex)
        import traceback; traceback.print_exc()
    print("[worker] Completed.")
