# # main.py — orchestrator: download up to MAX_PDFS new tender PDFs and record processed ones
# import os
# import time
# import pathlib
# import urllib.parse
# from dotenv import load_dotenv
# from scraper import create_driver, go_to_tenders_by_location, search_by_location_anantnag
# from downloader import download_pdf_from_detail

# load_dotenv()
# MAX_PDFS = int(os.getenv("MAX_PDFS", "10"))
# PROCESSED_FILE = "processed.txt"
# DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "pdfs")
# os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# def load_processed():
#     if not os.path.exists(PROCESSED_FILE):
#         return set()
#     with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
#         return set(line.strip() for line in f if line.strip())


# def save_processed(item):
#     with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
#         f.write(item + "\n")


# def extract_tender_id_from_link(link):
#     # fallback heuristic: use 'sp=' param if present, otherwise use full link
#     import urllib.parse as up
#     parsed = up.urlparse(link)
#     qs = up.parse_qs(parsed.query)
#     if "sp" in qs and qs["sp"]:
#         return qs["sp"][0]
#     return link


# def _unique_filename(path):
#     """
#     If path exists, append a timestamp suffix before the extension.
#     Returns the final unique path string.
#     """
#     p = pathlib.Path(path)
#     if not p.exists():
#         return str(p)
#     base = p.stem
#     ext = p.suffix or ""
#     ts = int(time.time())
#     new_name = f"{base}_{ts}{ext}"
#     return str(p.with_name(new_name))


# def get_canonical_tender_id(driver, detail_link, verbose=False):
#     """
#     Navigate to the tender detail link and try to extract a stable tender identifier,
#     preferably the 'Tender Reference Number' from the Basic Details block. Returns the
#     canonical id as string, or None if it couldn't be found.
#     NOTE: this function navigates the driver to the detail_link (and leaves it there).
#     """
#     try:
#         driver.get(detail_link)
#         time.sleep(0.8)
#         # look for a label "Tender Reference Number" and read the adjacent value
#         # Several fallbacks in case markup differs between pages.
#         xpaths = [
#             # common: a td containing the label, then following-sibling td
#             "//td[contains(normalize-space(.),'Tender Reference Number')]/following-sibling::td[1]",
#             # label inside <th> or <b> with following td
#             "//*[contains(normalize-space(.),'Tender Reference Number')]/following::td[1]",
#             # fallback: search for an element with text 'Ref.No' or 'Reference No' etc.
#             "//*[contains(translate(.,'REFERENCE NO','reference no'),'reference no')]/following::td[1]",
#             "//*[contains(translate(.,'TENDER REF','tender ref'),'tender ref')]/following::td[1]",
#         ]
#         for xp in xpaths:
#             try:
#                 el = driver.find_element("xpath", xp)
#                 txt = (el.text or "").strip()
#                 if txt:
#                     if verbose:
#                         print("Canonical tender id extracted via xpath:", xp, "->", txt)
#                     return txt
#             except Exception:
#                 continue

#         # Another fallback: try to read the page title / heading which often contains the tender id
#         try:
#             # many pages show "Tender Details" then the tender title; try to capture any 'Ref' text on the page
#             page_text = driver.page_source
#             # crude scan for "Ref" patterns (e.g., ENIT139of2025-26)
#             import re
#             m = re.search(r"(REF(?:ERENCE)?\s*[:#]?\s*[\w\-\/\.\_]+)", page_text, flags=re.IGNORECASE)
#             if m:
#                 txt = m.group(1).strip()
#                 return txt
#         except Exception:
#             pass

#     except Exception:
#         pass

#     return None


# def main():
#     processed = load_processed()
#     driver = create_driver()
#     try:
#         # 1) Open site and go to tenders-by-location page (you'll be prompted for search captcha)
#         go_to_tenders_by_location(driver)
#         links = search_by_location_anantnag(driver, manual_captcha=True)

#         # 2) Filter links that look like tender detail links and dedupe keeping order
#         # 2) Filter links that look like tender detail links and dedupe keeping order
#         detail_links = []
#         seen = set()
#         for l in links:
#             ll = (l or "").strip()
#             if not ll:
#                 continue
#             low = ll.lower()
#             # prefer explicit detail links only; skip helper/pagination links
#             if ("directlink_0" in low or "%24directlink_0" in low or "sp=" in low) \
#                and ("tablepages.link" not in low) and ("afrontendadvancedsearchresult" not in low):
#                 if ll not in seen:
#                     seen.add(ll)
#                     detail_links.append(ll)

#         # If user provided a specific single link via env variable, use only that
#         single = os.getenv("SINGLE_TENDER_LINK")
#         if single:
#             single = single.strip()
#             if single:
#                 print("SINGLE_TENDER_LINK set — overriding candidate list with single link.")
#                 detail_links = [single]

#         print("Found", len(detail_links), "detail links (candidates).")


#         downloaded = 0
#         failures = 0

#         # We'll iterate over detail_links and pick the first MAX_PDFS unique tenders
#         for link in detail_links:
#             if downloaded >= MAX_PDFS:
#                 print("Reached MAX_PDFS, stopping early.")
#                 break

#             # get a canonical id by visiting the detail page and reading Tender Reference Number
#             print("\nVisiting detail to extract canonical ID for link:", link)
#             canonical_id = None
#             try:
#                 canonical_id = get_canonical_tender_id(driver, link, verbose=False)
#             except Exception as e:
#                 print("Warning: couldn't extract canonical id by visiting page:", e)
#                 canonical_id = None

#             if not canonical_id:
#                 canonical_id = extract_tender_id_from_link(link)
#                 print("Using fallback canonical id from link:", canonical_id)
#             else:
#                 print("Canonical tender id:", canonical_id)

#             if canonical_id in processed:
#                 print("Skipping already processed tender (canonical id):", canonical_id)
#                 continue

#             # Now try to download the tender PDF(s) for this detail page
#             print("Processing tender (canonical id):", canonical_id)
#             success = False
#             # attempt several times (captcha/network may be flaky)
#             for attempt in range(1, 4):
#                 try:
#                     print(f"Attempt {attempt} for tender {canonical_id} ...")
#                     fname = download_pdf_from_detail(driver, link, manual=True, captcha_poll_timeout=120)

#                     if fname and os.path.exists(fname) and os.path.getsize(fname) > 1024:
#                         # ensure unique filename if needed
#                         final_name = _unique_filename(os.path.join(DOWNLOAD_DIR, os.path.basename(fname)))
#                         if final_name != fname:
#                             try:
#                                 os.replace(fname, final_name)
#                                 fname = final_name
#                             except Exception:
#                                 # ignore rename if it fails
#                                 pass
#                         print("✅ Downloaded and saved:", fname)
#                         save_processed(canonical_id)
#                         processed.add(canonical_id)
#                         downloaded += 1
#                         success = True
#                         # polite pause
#                         time.sleep(2.5)
#                         break
#                     else:
#                         # If downloader returned None or tiny file, consider retrying
#                         print("No valid PDF returned (None or too small).")
#                         try:
#                             if fname and os.path.exists(fname) and os.path.getsize(fname) < 1024:
#                                 os.remove(fname)
#                         except Exception:
#                             pass
#                 except Exception as e:
#                     print("Error while downloading tender:", e)
#                 # small backoff before retry
#                 time.sleep(0.8 + attempt * 0.5)

#             if not success:
#                 print("❌ Failed to download tender:", canonical_id)
#                 failures += 1
#                 # continue to next candidate

#         print("\nFinished. Downloaded:", downloaded, "new PDFs. Failures:", failures)
#     finally:
#         driver.quit()


# if __name__ == "__main__":
#     main()


# main.py — orchestrator: download up to requested number of new tender PDFs and record processed ones
import os
import time
import pathlib
import argparse
from dotenv import load_dotenv
from scraper import create_driver, go_to_tenders_by_location, search_by_location_anantnag
from downloader import download_pdf_from_detail

load_dotenv()

PROCESSED_FILE = "processed.txt"
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "pdfs")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def load_processed():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_processed(item):
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(item + "\n")


def _unique_filename(path):
    p = pathlib.Path(path)
    if not p.exists():
        return str(p)
    base = p.stem
    ext = p.suffix or ""
    ts = int(time.time())
    new_name = f"{base}_{ts}{ext}"
    return str(p.with_name(new_name))


def extract_tender_id_from_link(link):
    """Fallback heuristic: use 'sp=' param if present, otherwise return the full link."""
    import urllib.parse as up
    parsed = up.urlparse(link)
    qs = up.parse_qs(parsed.query)
    if "sp" in qs and qs["sp"]:
        return qs["sp"][0]
    return link


def get_canonical_tender_id(driver, detail_link, verbose=False):
    """
    Navigate to the tender detail link and try to extract a stable tender identifier,
    preferably the 'Tender Reference Number' from the Basic Details block.
    NOTE: this function navigates the driver to the detail_link (and leaves it there).
    """
    try:
        driver.get(detail_link)
        time.sleep(0.8)
        xpaths = [
            "//td[contains(normalize-space(.),'Tender Reference Number')]/following-sibling::td[1]",
            "//*[contains(normalize-space(.),'Tender Reference Number')]/following::td[1]",
            "//*[contains(translate(.,'REFERENCE NO','reference no'),'reference no')]/following::td[1]",
            "//*[contains(translate(.,'TENDER REF','tender ref'),'tender ref')]/following::td[1]",
        ]
        for xp in xpaths:
            try:
                el = driver.find_element("xpath", xp)
                txt = (el.text or "").strip()
                if txt:
                    if verbose:
                        print("Canonical tender id extracted via xpath:", xp, "->", txt)
                    return txt
            except Exception:
                continue

        # fallback: quick regex search in page source for typical Ref patterns
        try:
            page_text = driver.page_source or ""
            import re
            m = re.search(r"(ENIT[^\s<>\"']+|e-NIT[^\s<>\"']+|NIT\s*\d+[^\s<>\"']*|REF(?:ERENCE)?[:#]?\s*[A-Za-z0-9_\-\/\.]+)", page_text, flags=re.IGNORECASE)
            if m:
                txt = m.group(1).strip()
                return txt
        except Exception:
            pass

    except Exception:
        pass

    return None


def unique_candidates_by_canonical(driver, detail_links, target_count=1, verbose=False):
    """
    Visit detail_links in order, extract canonical id for each, and build a list
    of unique candidates (link, canonical_id). Stop once we have target_count unique ids.
    """
    candidates = []
    seen_ids = set()
    for link in detail_links:
        if len(candidates) >= target_count:
            break
        try:
            cid = get_canonical_tender_id(driver, link, verbose=verbose)
        except Exception:
            cid = None
        if not cid:
            cid = extract_tender_id_from_link(link)
        cid_norm = (cid or "").strip() or link
        if cid_norm in seen_ids:
            if verbose:
                print("Skipping duplicate canonical id (already seen):", cid_norm)
            continue
        seen_ids.add(cid_norm)
        candidates.append((link, cid_norm))
    return candidates


def main():
    parser = argparse.ArgumentParser(description="Download tender PDFs (unique tenders).")
    parser.add_argument("--num", "-n", type=int, default=None, help="Number of unique tenders to fetch")
    parser.add_argument("--single", "-s", type=str, default=None, help="Single specific detail link to fetch (overrides list)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if args.num is not None:
        max_pdfs = int(args.num)
    else:
        max_pdfs = int(os.getenv("MAX_PDFS", "10"))

    print("Starting tender scraping")
    print("Requested number of unique tenders:", max_pdfs)

    processed = load_processed()
    driver = create_driver()

    try:
        go_to_tenders_by_location(driver)
        links = search_by_location_anantnag(driver, manual_captcha=True)

        # Filter candidates (only explicit detail links)
        detail_links = []
        seen = set()
        for l in links:
            ll = (l or "").strip()
            if not ll:
                continue
            low = ll.lower()
            if ("directlink_0" in low or "%24directlink_0" in low or "sp=" in low) \
               and ("tablepages.link" not in low) and ("refresh" not in low):
                if ll not in seen:
                    seen.add(ll)
                    detail_links.append(ll)

        if args.single:
            detail_links = [args.single.strip()]
            print("Single link mode — processing only:", detail_links[0])

        print("Found", len(detail_links), "detail links (candidates). Resolving canonical IDs...")

        unique_cands = unique_candidates_by_canonical(driver, detail_links, target_count=max_pdfs, verbose=args.verbose)
        print("Unique tender candidates to process:", [(c, id) for c, id in unique_cands])

        downloaded = 0
        failures = 0

        for link, canonical_id in unique_cands:
            if downloaded >= max_pdfs:
                break

            if canonical_id in processed:
                print("Skipping already processed tender (canonical id):", canonical_id)
                continue

            print("Processing tender (canonical id):", canonical_id, "link:", link)
            success = False
            for attempt in range(1, 4):
                try:
                    print(f"Attempt {attempt} for tender {canonical_id} ...")
                    fname = download_pdf_from_detail(driver, link, manual=True, captcha_poll_timeout=120)
                    if fname and os.path.exists(fname) and os.path.getsize(fname) > 1024:
                        final_name = _unique_filename(pathlib.Path(DOWNLOAD_DIR) / pathlib.Path(fname).name)
                        if final_name != fname:
                            try:
                                os.replace(fname, final_name)
                                fname = final_name
                            except Exception:
                                pass
                        print("✅ Downloaded and saved:", fname)
                        save_processed(canonical_id)
                        processed.add(canonical_id)
                        downloaded += 1
                        success = True
                        time.sleep(2.5)
                        break
                    else:
                        print("No valid PDF returned (None or too small).")
                        try:
                            if fname and os.path.exists(fname) and os.path.getsize(fname) < 1024:
                                os.remove(fname)
                        except Exception:
                            pass
                except Exception as e:
                    print("Error while downloading tender:", e)
                time.sleep(0.8 + attempt * 0.5)

            if not success:
                print("❌ Failed to download tender:", canonical_id)
                failures += 1

        print("\nFinished. Downloaded:", downloaded, "new PDFs. Failures:", failures)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
