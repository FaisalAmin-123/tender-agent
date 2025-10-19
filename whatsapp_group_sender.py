

# import os, time, sys, re
# from dotenv import load_dotenv
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from pathlib import Path

# load_dotenv()

# CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "chromedriver")
# PDF_DIR = os.getenv("DOWNLOAD_DIR", os.getenv("PDF_DIR", "pdfs"))
# CHROME_PROFILE_DIR = os.getenv("CHROME_PROFILE_DIR", "chrome-data")
# WAIT_SHORT = 1.0
# WAIT_LONG = 30.0

# # ---- Driver creation (shared) ----
# def _create_driver(headless=False):
#     opts = webdriver.ChromeOptions()
#     profile_dir = os.path.abspath(CHROME_PROFILE_DIR)
#     os.makedirs(profile_dir, exist_ok=True)
#     opts.add_argument(f"--user-data-dir={profile_dir}")
#     opts.add_experimental_option("excludeSwitches", ["enable-automation"])
#     opts.add_experimental_option("useAutomationExtension", False)
#     if not headless:
#         opts.add_argument("--start-maximized")
#     else:
#         opts.add_argument("--headless=new")
#         opts.add_argument("--window-size=1200,900")
#     service = Service(CHROMEDRIVER_PATH)
#     driver = webdriver.Chrome(service=service, options=opts)
#     return driver

# # ---- Utilities from your original script (slightly refactored) ----
# def wait_for_whatsapp_ready(driver, timeout=120):
#     driver.get("https://web.whatsapp.com")
#     wait = WebDriverWait(driver, timeout)
#     selectors = [
#         "//div[@contenteditable='true' and @data-tab and (@data-tab='3' or @data-tab='4' or @data-tab='6')]",
#         "//div[@contenteditable='true' and @role='textbox']",
#     ]
#     for sel in selectors:
#         try:
#             wait.until(EC.presence_of_element_located((By.XPATH, sel)))
#             return True
#         except Exception:
#             continue
#     # final attempt after asking user to scan
#     try:
#         for sel in selectors:
#             wait.until(EC.presence_of_element_located((By.XPATH, sel)))
#             return True
#     except Exception:
#         return False

# def _collect_visible_chat_titles(driver):
#     titles = []
#     try:
#         try:
#             pane = driver.find_element(By.ID, "pane-side")
#             for _ in range(6):
#                 driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + 400", pane)
#                 time.sleep(0.12)
#         except Exception:
#             pass
#         spans = driver.find_elements(By.XPATH, "//span[@title]")
#         seen = set()
#         for s in spans:
#             try:
#                 t = s.get_attribute("title")
#                 if t and t.strip() and t not in seen:
#                     seen.add(t)
#                     titles.append(t.strip())
#             except:
#                 continue
#     except Exception:
#         pass
#     return titles

# def _normalize(s):
#     s2 = (s or "").lower()
#     s2 = re.sub(r'[\W_]+', '', s2)
#     s2 = re.sub(r'\s+', '', s2)
#     return s2

# def _get_displayed_chat_header(driver):
#     try:
#         xpaths = [
#             "//div[@id='main']//header//span[@title]",
#             "//header//div//span[@title]",
#             "//div[@id='main']//header//*[contains(@class,'_21nHd') or contains(@class,'_1hI5g')]",
#             "//div[@id='main']//header//div[@dir='auto']",
#         ]
#         for xp in xpaths:
#             try:
#                 el = driver.find_element(By.XPATH, xp)
#                 txt = el.get_attribute("title") or el.text or ""
#                 txt = txt.strip()
#                 if txt:
#                     return txt
#             except Exception:
#                 continue
#         # fallback
#         try:
#             header = driver.find_element(By.XPATH, "//div[@id='main']//header")
#             txt = header.text or ""
#             txt = txt.strip().splitlines()[0] if txt else ""
#             if txt:
#                 return txt
#         except Exception:
#             pass
#     except Exception:
#         pass
#     return None

# def open_group_and_confirm(driver, group_name):
#     wait = WebDriverWait(driver, WAIT_LONG)
#     # fast exact match
#     try:
#         group_xpath = f"//span[@title=\"{group_name}\"]"
#         els = driver.find_elements(By.XPATH, group_xpath)
#         if els:
#             for el in els:
#                 try:
#                     el.click(); time.sleep(0.8)
#                     header = _get_displayed_chat_header(driver)
#                     if header and (header == group_name or group_name.lower() in header.lower() or header.lower() in group_name.lower()):
#                         return True
#                 except Exception:
#                     continue
#     except Exception:
#         pass

#     titles = _collect_visible_chat_titles(driver)
#     if not titles:
#         return False

#     candidates = []
#     for t in titles:
#         if t == group_name:
#             candidates.append(t)
#     for t in titles:
#         if t.lower() == group_name.lower() and t not in candidates:
#             candidates.append(t)
#     ng = _normalize(group_name)
#     for t in titles:
#         if ng and _normalize(t) == ng and t not in candidates:
#             candidates.append(t)
#     for t in titles:
#         if (group_name.lower() in t.lower() or t.lower() in group_name.lower()) and t not in candidates:
#             candidates.append(t)
#     words = [w for w in group_name.lower().split() if w]
#     for t in titles:
#         tl = t.lower()
#         if all(w in tl for w in words) and t not in candidates:
#             candidates.append(t)
#     for t in titles:
#         if t not in candidates:
#             candidates.append(t)

#     attempted = set()
#     for cand in candidates:
#         if cand in attempted:
#             continue
#         attempted.add(cand)
#         try:
#             el = driver.find_element(By.XPATH, f"//span[@title=\"{cand}\"]")
#             driver.execute_script("arguments[0].click();", el)
#             time.sleep(0.9)
#             header = _get_displayed_chat_header(driver)
#             if header:
#                 lowh = header.lower()
#                 if "announcement" in lowh or "announcements" in lowh or "community" in lowh:
#                     continue
#                 if header == cand or cand.lower() in header.lower() or header.lower() in cand.lower() or group_name.lower() in header.lower() or header.lower() in group_name.lower():
#                     return True
#         except Exception:
#             continue
#     return False

# def _open_attach_menu(driver):
#     attach_selectors = [
#         ("css", "span[data-icon='clip']"),
#         ("xpath", "//div[@data-icon='clip']"),
#         ("xpath", "//div[@title='Attach']"),
#         ("xpath", "//button[@aria-label='Attach']"),
#         ("xpath", "//span[@data-testid='clip']"),
#         ("xpath", "//div[@role='button' and contains(@aria-label,'Attach')]"),
#     ]
#     for mode, sel in attach_selectors:
#         try:
#             if mode == "css":
#                 els = driver.find_elements(By.CSS_SELECTOR, sel)
#             else:
#                 els = driver.find_elements(By.XPATH, sel)
#             for el in els:
#                 try:
#                     if not el.is_displayed():
#                         continue
#                     try:
#                         el.click()
#                     except Exception:
#                         try:
#                             driver.execute_script("arguments[0].click();", el)
#                         except:
#                             continue
#                     WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
#                     return True
#                 except Exception:
#                     continue
#         except Exception:
#             continue
#     return False

# def _send_files_to_current_chat(driver, filepaths):
#     sent = []
#     for path in filepaths:
#         p = str(Path(path).resolve())
#         if not os.path.exists(p):
#             continue
#         try:
#             try:
#                 WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.XPATH, "//footer")))
#             except Exception:
#                 pass

#             opened = False
#             for attempt in range(1, 4):
#                 if _open_attach_menu(driver):
#                     opened = True
#                     break
#                 time.sleep(0.6)
#             if not opened:
#                 continue

#             inputs = WebDriverWait(driver, 6).until(EC.presence_of_all_elements_located((By.XPATH, "//input[@type='file']")))
#             file_input = None
#             for inp in inputs:
#                 try:
#                     if inp.is_displayed():
#                         file_input = inp
#                         break
#                 except:
#                     continue
#             if not file_input and inputs:
#                 file_input = inputs[0]
#             if not file_input:
#                 continue

#             file_input.send_keys(p)
#             time.sleep(0.9)

#             # optional caption
#             try:
#                 caption_elem = driver.find_element(By.XPATH, "//div[@contenteditable='true' and @data-tab]")
#                 caption_text = f"{Path(p).name}\nTender notice"
#                 caption_elem.click()
#                 caption_elem.send_keys(caption_text)
#                 time.sleep(0.25)
#             except Exception:
#                 pass

#             try:
#                 send_btn = driver.find_element(By.CSS_SELECTOR, "span[data-icon='send']")
#                 driver.execute_script("arguments[0].click();", send_btn)
#             except Exception:
#                 try:
#                     caption_elem.send_keys(Keys.ENTER)
#                 except Exception:
#                     pass

#             size_mb = os.path.getsize(p) / (1024 * 1024)
#             extra_wait = 2.0 + min(14, size_mb * 1.2)
#             time.sleep(extra_wait)
#             sent.append(p)
#         except Exception:
#             continue
#     return sent

# def gather_recent_pdfs(limit=10):
#     d = Path(PDF_DIR)
#     if not d.exists():
#         return []
#     files = sorted([p for p in d.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"], key=lambda x: x.stat().st_mtime, reverse=True)
#     return [str(p) for p in files[:limit]]

# # ---- Public API functions ----

# def list_visible_groups(timeout=20):
#     """
#     Return a list of visible chat titles from WhatsApp Web.
#     - timeout: seconds to wait for WhatsApp to be ready/loaded.
#     """
#     driver = _create_driver(headless=False)
#     try:
#         ok = wait_for_whatsapp_ready(driver, timeout=timeout)
#         if not ok:
#             raise RuntimeError("WhatsApp Web not ready. Please scan QR in opened Chrome window.")
#         titles = _collect_visible_chat_titles(driver)
#         return titles
#     finally:
#         try:
#             driver.quit()
#         except:
#             pass

# def send_recent_pdfs_to_group(group_name, limit=5, timeout=60):
#     """
#     Send the most recent 'limit' PDFs from PDF_DIR to the given group_name.
#     Returns dict with keys: sent (list), skipped (list), error (optional)
#     - group_name: string name of group to open/confirm
#     - limit: how many recent PDFs to send
#     - timeout: overall timeout for WhatsApp readiness and operations
#     """
#     driver = _create_driver(headless=False)
#     result = {"sent": [], "skipped": [], "error": None}
#     try:
#         ok = wait_for_whatsapp_ready(driver, timeout=30)
#         if not ok:
#             result["error"] = "WhatsApp Web not ready (scan QR in the opened Chrome window)."
#             return result

#         opened = open_group_and_confirm(driver, group_name)

#         if not opened:
#             result["error"] = f"Could not locate or open group: {group_name}"
#             return result

#         pdfs = gather_recent_pdfs(limit)
#         if not pdfs:
#             result["skipped"] = []
#             return result

#         sent = _send_files_to_current_chat(driver, pdfs)
#         result["sent"] = sent
#         # files that were meant to be sent but were not
#         result["skipped"] = [p for p in pdfs if p not in sent]
#         return result
#     except Exception as e:
#         result["error"] = str(e)
#         return result
#     finally:
#         try:
#             driver.quit()
#         except:
#             pass

# # Keep CLI behaviour for backward compatibility
# def main(group_name=None):
#     """
#     Send PDFs to WhatsApp group
    
#     Args:
#         group_name: Name of the WhatsApp group (if None, uses .env default)
#     """
#     if group_name is None:
#         group_name = os.getenv("WHATSAPP_GROUP_NAME")
    
#     print("WhatsApp group sender starting. Group:", group_name)
#     if not group:
#         print("WHATSAPP_GROUP_NAME not set in .env. Use this script to pick a group interactively.")
#         print("Opening WhatsApp Web to let you choose group in the browser. After that the CLI will send recent PDFs.")
#         # list groups for user to choose
#         titles = list_visible_groups(timeout=40)
#         if not titles:
#             print("No visible chats found. Make sure WhatsApp Web is logged in.")
#             return
#         print("Visible chats (first 20):")
#         for i, t in enumerate(titles[:20], 1):
#             print(f"{i}. {t}")
#         try:
#             sel = input("Enter exact group name or number to send to (or press Enter to cancel): ").strip()
#         except Exception:
#             sel = ""
#         chosen = None
#         if sel.isdigit():
#             idx = int(sel) - 1
#             if 0 <= idx < len(titles):
#                 chosen = titles[idx]
#         elif sel:
#             chosen = sel
#         if not chosen:
#             print("No group chosen; exiting.")
#             return
#         group = chosen

#     print("Sending recent PDFs to group:", group)
#     res = send_recent_pdfs_to_group(group_name=group, limit=int(os.getenv("MAX_PDFS", "5")), timeout=60)
#     print("Result:", res)

# if __name__ == "__main__":
#     main()


# whatsapp_group_sender.py
# Robust group selection and programmatic sending of PDFs to a WhatsApp group.
import os, time, sys, re
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path

load_dotenv()

CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "chromedriver")
ENV_GROUP_NAME = os.getenv("WHATSAPP_GROUP_NAME", "").strip()
PDF_DIR = os.getenv("DOWNLOAD_DIR", os.getenv("PDF_DIR", "pdfs"))
MAX_FILES = int(os.getenv("MAX_PDFS", "10"))
CHROME_PROFILE_DIR = os.getenv("CHROME_PROFILE_DIR", "chrome-data")
WAIT_SHORT = 1.0
WAIT_LONG = 30.0

def create_driver(headless=False):
    opts = webdriver.ChromeOptions()
    profile_dir = os.path.abspath(CHROME_PROFILE_DIR)
    os.makedirs(profile_dir, exist_ok=True)
    opts.add_argument(f"--user-data-dir={profile_dir}")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--start-maximized")
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=opts)
    return driver

def wait_for_whatsapp_ready(driver, timeout=120):
    driver.get("https://web.whatsapp.com")
    wait = WebDriverWait(driver, timeout)
    selectors = [
        "//div[@contenteditable='true' and @data-tab and (@data-tab='3' or @data-tab='4' or @data-tab='6')]",
        "//div[@contenteditable='true' and @role='textbox']",
    ]
    for sel in selectors:
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, sel)))
            return True
        except Exception:
            continue
    # second chance
    try:
        for sel in selectors:
            wait.until(EC.presence_of_element_located((By.XPATH, sel)))
            return True
    except Exception:
        return False

def _collect_visible_chat_titles(driver):
    titles = []
    try:
        try:
            pane = driver.find_element(By.ID, "pane-side")
            for _ in range(6):
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + 400", pane)
                time.sleep(0.12)
        except Exception:
            pass
        spans = driver.find_elements(By.XPATH, "//span[@title]")
        seen = set()
        for s in spans:
            try:
                t = s.get_attribute("title")
                if t and t.strip() and t not in seen:
                    seen.add(t)
                    titles.append(t.strip())
            except:
                continue
    except Exception:
        pass
    return titles

def _normalize(s):
    s2 = (s or "").lower()
    s2 = re.sub(r'[\W_]+', '', s2)
    s2 = re.sub(r'\s+', '', s2)
    return s2

def _get_displayed_chat_header(driver, timeout=6):
    try:
        xpaths = [
            "//div[@id='main']//header//span[@title]",
            "//header//div//span[@title]",
            "//div[@id='main']//header//*[contains(@class,'_21nHd') or contains(@class,'_1hI5g')]",
            "//div[@id='main']//header//div[@dir='auto']",
        ]
        for xp in xpaths:
            try:
                el = driver.find_element(By.XPATH, xp)
                txt = el.get_attribute("title") or el.text or ""
                txt = txt.strip()
                if txt:
                    return txt
            except Exception:
                continue
        try:
            header = driver.find_element(By.XPATH, "//div[@id='main']//header")
            txt = header.text or ""
            txt = txt.strip().splitlines()[0] if txt else ""
            if txt:
                return txt
        except Exception:
            pass
    except Exception:
        pass
    return None

def open_group_and_confirm(driver, group_name):
    wait = WebDriverWait(driver, WAIT_LONG)

    # try exact-match clickable spans
    try:
        group_xpath = f"//span[@title=\"{group_name}\"]"
        els = driver.find_elements(By.XPATH, group_xpath)
        if els:
            for el in els:
                try:
                    el.click()
                    time.sleep(0.8)
                    header = _get_displayed_chat_header(driver)
                    if header and (header == group_name or group_name.lower() in header.lower() or header.lower() in group_name.lower()):
                        return True
                except Exception:
                    continue
    except Exception:
        pass

    titles = _collect_visible_chat_titles(driver)
    if not titles:
        return False

    candidates = []
    for t in titles:
        if t == group_name:
            candidates.append(t)
    for t in titles:
        if t.lower() == group_name.lower() and t not in candidates:
            candidates.append(t)
    ng = _normalize(group_name)
    for t in titles:
        if ng and _normalize(t) == ng and t not in candidates:
            candidates.append(t)
    for t in titles:
        if (group_name.lower() in t.lower() or t.lower() in group_name.lower()) and t not in candidates:
            candidates.append(t)
    words = [w for w in group_name.lower().split() if w]
    for t in titles:
        tl = t.lower()
        if all(w in tl for w in words) and t not in candidates:
            candidates.append(t)
    for t in titles:
        if t not in candidates:
            candidates.append(t)

    attempted = set()
    for cand in candidates:
        if cand in attempted:
            continue
        attempted.add(cand)
        try:
            el = driver.find_element(By.XPATH, f"//span[@title=\"{cand}\"]")
            driver.execute_script("arguments[0].click();", el)
            time.sleep(0.9)
            header = _get_displayed_chat_header(driver)
            if header:
                lowh = header.lower()
                if "announcement" in lowh or "announcements" in lowh or "community" in lowh:
                    continue
                if header == cand or cand.lower() in header.lower() or header.lower() in cand.lower() or (group_name and group_name.lower() in header.lower()) or (group_name and header.lower() in group_name.lower()):
                    return True
        except Exception:
            continue
    return False

def _open_attach_menu(driver, timeout=8):
    attach_selectors = [
        ("css", "span[data-icon='clip']"),
        ("xpath", "//div[@data-icon='clip']"),
        ("xpath", "//div[@title='Attach']"),
        ("xpath", "//button[@aria-label='Attach']"),
        ("xpath", "//span[@data-testid='clip']"),
        ("xpath", "//div[@role='button' and contains(@aria-label,'Attach')]"),
    ]
    for mode, sel in attach_selectors:
        try:
            if mode == "css":
                els = driver.find_elements(By.CSS_SELECTOR, sel)
            else:
                els = driver.find_elements(By.XPATH, sel)
            for el in els:
                try:
                    if not el.is_displayed():
                        continue
                    try:
                        el.click()
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", el)
                        except:
                            continue
                    WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
                    return True
                except Exception:
                    continue
        except Exception:
            continue
    return False

def send_files_to_current_chat(driver, filepaths):
    sent = []
    for path in filepaths:
        p = str(Path(path).resolve())
        if not os.path.exists(p):
            continue
        try:
            try:
                WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.XPATH, "//footer")))
            except Exception:
                pass

            opened = False
            for attempt in range(1, 4):
                if _open_attach_menu(driver, timeout=6):
                    opened = True
                    break
                time.sleep(0.6)

            if not opened:
                continue

            inputs = WebDriverWait(driver, 6).until(EC.presence_of_all_elements_located((By.XPATH, "//input[@type='file']")))
            file_input = None
            for inp in inputs:
                try:
                    if inp.is_displayed():
                        file_input = inp
                        break
                except:
                    continue
            if not file_input and inputs:
                file_input = inputs[0]

            if not file_input:
                continue

            file_input.send_keys(p)
            time.sleep(0.9)

            try:
                caption_elem = driver.find_element(By.XPATH, "//div[@contenteditable='true' and @data-tab]")
                caption_text = f"{Path(p).name}\nTender notice"
                caption_elem.click()
                caption_elem.send_keys(caption_text)
                time.sleep(0.25)
            except Exception:
                pass

            try:
                send_btn = driver.find_element(By.CSS_SELECTOR, "span[data-icon='send']")
                driver.execute_script("arguments[0].click();", send_btn)
            except Exception:
                try:
                    caption_elem.send_keys(Keys.ENTER)
                except Exception:
                    pass

            size_mb = os.path.getsize(p) / (1024 * 1024)
            extra_wait = 2.0 + min(14, size_mb * 1.2)
            time.sleep(extra_wait)
            sent.append(p)
        except Exception:
            continue
    return sent

def gather_recent_pdfs(limit=10):
    d = Path(PDF_DIR)
    if not d.exists():
        return []
    files = sorted([p for p in d.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"], key=lambda x: x.stat().st_mtime, reverse=True)
    return [str(p) for p in files[:limit]]

def send_recent_pdfs_to_group(group_name=None, limit=10, headless=False):
    """
    Programmatic entrypoint used by the API.
    - group_name: group to open (string). If None or empty, falls back to ENV_GROUP_NAME.
    - limit: number of recent pdfs to send.
    Returns a dict: {"sent": [...], "errors": [...], "selected_group": str or None}
    """
    chosen_group = (group_name or "").strip() or (ENV_GROUP_NAME or "").strip()
    result = {"sent": [], "errors": [], "selected_group": chosen_group}

    pdfs = gather_recent_pdfs(limit)
    if not pdfs:
        result["errors"].append("No PDF files found to send.")
        return result

    driver = None
    try:
        driver = create_driver(headless=headless)
        ok = wait_for_whatsapp_ready(driver, timeout=60)
        if not ok:
            result["errors"].append("WhatsApp Web not ready. Scan QR on the server's WhatsApp session.")
            return result

        if not chosen_group:
            result["errors"].append("No group specified and no default configured in environment.")
            return result

        opened = open_group_and_confirm(driver, chosen_group)
        if not opened:
            result["errors"].append(f"Could not open or confirm group: {chosen_group}")
            return result

        sent = send_files_to_current_chat(driver, pdfs)
        result["sent"] = sent
        if not sent:
            result["errors"].append("No files were successfully sent. Check attach/menu selectors or network.")
    except Exception as e:
        result["errors"].append(str(e))
    finally:
        try:
            if driver:
                driver.quit()
        except:
            pass

    return result
def send_files_to_group(group_name: str, max_files: int = 10):
    """
    Programmatic entry point for sending tender PDFs to a specific WhatsApp group.
    This is used by api_worker.py instead of running interactively.
    """
    sent = []
    driver = None
    try:
        print(f"[send_files_to_group] Starting: group='{group_name}', max_files={max_files}")
        driver = create_driver()
        
        ok = wait_for_whatsapp_ready(driver, timeout=90)
        if not ok:
            print("[send_files_to_group] WhatsApp Web not ready — please ensure the profile is logged in.")
            return sent

        # Try to open the given group name
        opened = open_group_and_confirm(driver, group_name)
        if not opened:
            print(f"[send_files_to_group] ❌ Could not open WhatsApp group: '{group_name}'")
            return sent

        # Collect PDFs to send
        pdfs = gather_recent_pdfs(limit=max_files)
        if not pdfs:
            print("[send_files_to_group] ⚠️ No PDFs found to send.")
            return sent

        print(f"[send_files_to_group] Found {len(pdfs)} PDF(s): {[p for p in pdfs]}")
        sent = send_files_to_current_chat(driver, pdfs)
        print(f"[send_files_to_group] ✅ Sent files: {sent}")
        return sent

    except Exception as e:
        print(f"[send_files_to_group] ERROR: {e}")
        import traceback; traceback.print_exc()
        return sent
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def main():
    # Legacy CLI-friendly main: open default group and send MAX_FILES
    group = ENV_GROUP_NAME or ""
    res = send_recent_pdfs_to_group(group_name=group, limit=MAX_FILES, headless=False)
    print("WhatsApp send result:", res)
    return res

if __name__ == "__main__":
    main()
