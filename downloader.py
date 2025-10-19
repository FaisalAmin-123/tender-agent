
import os
import time
import urllib.parse
import tempfile
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from scraper import create_driver

load_dotenv()
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "pdfs")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def cookies_to_session(driver):
    s = requests.Session()
    for c in driver.get_cookies():
        try:
            if c.get("domain"):
                s.cookies.set(c["name"], c["value"], domain=c.get("domain"))
            else:
                s.cookies.set(c["name"], c["value"])
        except Exception:
            pass
    try:
        ua = driver.execute_script("return navigator.userAgent;")
        if ua:
            s.headers.update({"User-Agent": ua})
    except Exception:
        pass
    s.headers.setdefault("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    s.headers.setdefault("Accept-Language", "en-US,en;q=0.9")
    return s


def save_page_dump(driver, fname="page_dump.html"):
    try:
        with open(fname, "w", encoding="utf-8") as f:
            f.write(driver.page_source or "<no page_source>")
        print("Saved page dump to:", fname)
    except Exception as e:
        print("Failed saving page dump:", e)


def _download_via_requests(session, href, referer=None):
    if not href:
        return None
    try:
        headers = {}
        if referer:
            headers["Referer"] = referer
        r = session.get(href, timeout=30, stream=True, headers=headers, allow_redirects=True)
    except Exception as e:
        print("Request GET failed for", href, ":", e)
        return None

    print("HTTP", r.status_code, "for", href)
    content_type = (r.headers.get("content-type") or "").lower()
    content_disp = (r.headers.get("content-disposition") or "")

    if r.status_code != 200:
        return None

    looks_like_pdf = ("pdf" in content_type) or (".pdf" in content_disp.lower()) or href.lower().endswith(".pdf")
    if not looks_like_pdf:
        print("Request returned non-PDF content for", href, "content-type:", content_type)
        try:
            snippet = r.content[:1600]
            path = os.path.join(DOWNLOAD_DIR, "last_nonpdf_response.html")
            with open(path, "wb") as f:
                f.write(snippet)
            print("Saved snippet of non-PDF response to:", path)
        except Exception:
            pass
        return None

    filename = None
    try:
        if "filename=" in content_disp.lower():
            import re
            m = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)', content_disp, flags=re.IGNORECASE)
            if m:
                filename = m.group(1).strip().strip('"').strip("'")
    except Exception:
        filename = None

    if not filename:
        parsed = urllib.parse.urlparse(href)
        filename = os.path.basename(parsed.path) or f"tender_{int(time.time())}.pdf"

    # Compose target path and ensure uniqueness to avoid overwriting files with same name
    out = os.path.join(DOWNLOAD_DIR, filename)
    base, ext = os.path.splitext(out)
    # if file exists, create a unique name using timestamp + counter
    if os.path.exists(out):
        # prefer timestamp on first collision to match your previous behavior (makes debugging easier)
        ts = int(time.time())
        unique_out = f"{base}_{ts}{ext}"
        counter = 1
        while os.path.exists(unique_out):
            counter += 1
            unique_out = f"{base}_{ts}_{counter}{ext}"
        out = unique_out

    try:
        with open(out, "wb") as f:
            for chunk in r.iter_content(1024 * 16):
                if chunk:
                    f.write(chunk)
        print("Saved PDF via requests to:", out)
        return out

    except Exception as e:
        print("Failed saving file:", e)
        return None


def _collect_doc_section_hrefs(driver):
    results = []
    xpath_candidates = [
        "//*[contains(translate(.,'TENDERS DOCUMENTS','tenders documents'),'tenders documents')]",
        "//*[contains(translate(.,'TENDER DOCUMENTS','tender documents'),'tender documents')]",
        "//*[contains(translate(.,'DOCUMENTS','documents'),'documents') and (contains(translate(.,'TENDER','tender'),'tender'))]"
    ]
    doc_section = None
    for xp in xpath_candidates:
        try:
            doc_section = driver.find_element(By.XPATH, xp)
            if doc_section:
                break
        except Exception:
            doc_section = None

    if not doc_section:
        return results

    try:
        rows = doc_section.find_elements(By.XPATH, ".//tr")
        for r in rows:
            try:
                tds_with_pdf = r.find_elements(By.XPATH, ".//td[contains(translate(.,'.PDF','.pdf'),'.pdf')]")
                if tds_with_pdf:
                    for td in tds_with_pdf:
                        anchors = td.find_elements(By.TAG_NAME, "a")
                        for a in anchors:
                            try:
                                href = (a.get_attribute("href") or "").strip()
                                text = (a.text or "").strip()
                                if href or text:
                                    results.append((href, text))
                            except StaleElementReferenceException:
                                continue
                    continue

                anchors = r.find_elements(By.XPATH, ".//a[contains(translate(.,'.PDF','.pdf'),'.pdf')]")
                for a in anchors:
                    try:
                        href = (a.get_attribute("href") or "").strip()
                        text = (a.text or "").strip()
                        if href or text:
                            results.append((href, text))
                    except StaleElementReferenceException:
                        continue
            except StaleElementReferenceException:
                continue
    except Exception:
        try:
            anchors = doc_section.find_elements(By.TAG_NAME, "a")
            for a in anchors:
                try:
                    href = (a.get_attribute("href") or "").strip()
                    text = (a.text or "").strip()
                    results.append((href, text))
                except StaleElementReferenceException:
                    continue
        except Exception:
            pass

    return results


def _collect_generic_candidate_hrefs(driver):
    candidates = []
    for a in driver.find_elements(By.TAG_NAME, "a"):
        try:
            href = (a.get_attribute("href") or "").strip()
            onclick = (a.get_attribute("onclick") or "").lower()
            text = (a.text or "").strip()
            title = (a.get_attribute("title") or "") or ""
            alt = (a.get_attribute("alt") or "") or ""
        except StaleElementReferenceException:
            continue

        lowhref = href.lower()
        lowtext = (text or "").lower()
        lowtitle = (title or "").lower()
        lowalt = (alt or "").lower()

        if lowhref.endswith(".pdf") or lowhref.endswith(".doc") or lowhref.endswith(".docx"):
            candidates.append((href, text))
            continue
        if "docdownload" in lowhref or "docdownload" in onclick:
            candidates.append((href, text))
            continue
        if "download" in lowtext or "download" in lowtitle or "download" in lowalt:
            candidates.append((href, text))
            continue
        if "attachment" in lowhref or "attachmentid" in lowhref or "component=frontenddocument" in lowhref:
            candidates.append((href, text))
            continue
    return candidates


def _save_captcha_image_from_element(img_element, out_path):
    try:
        src = img_element.get_attribute("src") or ""
        if src.startswith("data:image"):
            try:
                header, b64 = src.split(",", 1)
                pad = (-len(b64)) % 4
                if pad:
                    b64 = b64 + ("=" * pad)
                data = base64.b64decode(b64)
                with open(out_path, "wb") as f:
                    f.write(data)
                return True
            except Exception as e:
                print("Base64 decode failed, will try element screenshot. Error:", e)
        try:
            img_element.screenshot(out_path)
            return True
        except Exception as e:
            print("Element screenshot failed:", e)
        if src.startswith("http"):
            try:
                r = requests.get(src, timeout=15)
                if r.status_code == 200:
                    with open(out_path, "wb") as f:
                        f.write(r.content)
                    return True
            except Exception as e:
                print("Download attempt of captcha src failed:", e)
    except Exception as e:
        print("Failed saving captcha image from element:", e)
    return False


def _find_pdf_on_page(driver):
    session = cookies_to_session(driver)
    try:
        for b in driver.find_elements(By.TAG_NAME, "a"):
            try:
                href2 = b.get_attribute("href") or ""
            except StaleElementReferenceException:
                continue
            if href2 and href2.lower().endswith(".pdf"):
                out = _download_via_requests(session, href2, referer=driver.current_url)
                if out:
                    return out
    except Exception:
        pass
    return None


def _poll_for_pdf_or_popup_close(driver, original_popup_handle, detail_url, timeout=60, interval=1.0):
    """
    Poll WITHOUT refreshing the detail page. Return downloaded file path or None.
    Succeeds when either:
      - a PDF link appears on the detail page (and downloads)
      - the popup window is closed by the user (we then search the detail page once more)
    """
    start = time.time()
    while time.time() - start < timeout:
        # First: if popup closed, break and inspect detail page
        if original_popup_handle not in driver.window_handles:
            # popup closed by user -> check page for pdf link
            try:
                # switch to original window if necessary
                driver.switch_to.window(driver.window_handles[0])
            except Exception:
                pass
            out = _find_pdf_on_page(driver)
            if out:
                return out
            # if not found yet, continue waiting a little (user may click submit and server may take time)
            # but DO NOT refresh page (refresh can cause captcha to reappear)
        else:
            # popup still open -> check if a pdf link has appeared on detail page (user may have solved in popup)
            try:
                # switch to original/parent window temporarily to inspect anchors (do NOT refresh)
                parent = driver.window_handles[0]
                driver.switch_to.window(parent)
                out = _find_pdf_on_page(driver)
                if out:
                    return out
                # switch back to popup to avoid losing focus expectation
                driver.switch_to.window(original_popup_handle)
            except Exception:
                pass
        time.sleep(interval)
    return None


def _poll_for_pdf_after_manual_submit_same_window(driver, detail_url, timeout=60, interval=1.0):
    """
    For same-window captcha: poll WITHOUT refreshing for either:
      - pdf link appears
      - captcha image element disappears/replaced (indicating submission)
    """
    start = time.time()
    while time.time() - start < timeout:
        out = _find_pdf_on_page(driver)
        if out:
            return out
        # check if captcha image is gone or replaced
        try:
            imgs = driver.find_elements(By.XPATH, "//img[contains(translate(@src,'CAPTCHA','captcha'),'captcha') or contains(@id,'captcha') or contains(@class,'captcha')]")
            if not imgs:
                # captcha image vanished -> re-check anchors once more (do not refresh)
                out = _find_pdf_on_page(driver)
                if out:
                    return out
        except Exception:
            pass
        time.sleep(interval)
    return None


def download_pdf_from_detail(driver, detail_url, manual=True, captcha_poll_timeout=60):
    driver.get(detail_url)
    time.sleep(1.0)

    page_low = (driver.page_source or "").lower()
    if not ("tender details" in page_low or "tenders documents" in page_low or "tender documents" in page_low):
        try:
            try:
                link = driver.find_element(By.XPATH, "//a[contains(@href,'DirectLink_0') or contains(@href,'%24DirectLink_0')]")
                link.click(); time.sleep(1.2)
            except Exception:
                try:
                    link = driver.find_element(By.XPATH, "//a[starts-with(normalize-space(.),'[')]")
                    link.click(); time.sleep(1.2)
                except Exception:
                    save_page_dump(driver, "page_before_detail.html")
                    raise RuntimeError("Not on tender detail page — saved page_before_detail.html for inspection.")
        except Exception as e:
            save_page_dump(driver, "page_before_detail.html")
            raise RuntimeError("Not on tender detail page — saved page_before_detail.html for inspection.") from e

    session = cookies_to_session(driver)

    # try direct pdf anchors first
    out = _find_pdf_on_page(driver)
    if out:
        return out

    doc_hrefs = _collect_doc_section_hrefs(driver)
    candidates = []
    for href, text in doc_hrefs:
        if (text and '.pdf' in text.lower()) or (href and href.lower().endswith('.pdf')):
            candidates.append((href, text))
    if not candidates and doc_hrefs:
        candidates = doc_hrefs.copy()

    if not candidates:
        candidates = _collect_generic_candidate_hrefs(driver)

    seen = set(); filtered = []
    for href, text in candidates:
        key = href or text
        if key not in seen:
            seen.add(key); filtered.append((href, text))
    candidates = filtered

    if not candidates:
        save_page_dump(driver, "page_no_download_candidates.html")
        raise RuntimeError("No download link candidates found on tender detail page. Page dumped to page_no_download_candidates.html")

    original_handle = driver.current_window_handle

    for idx, (href, text) in enumerate(candidates, start=1):
        print(f"Trying candidate {idx}: href={href} text='{(text or '')[:80]}'")
        try:
            # Try requests download first
            if href and (href.startswith("http://") or href.startswith("https://")):
                out = _download_via_requests(session, href, referer=detail_url)
                if out:
                    return out
                # navigate to href to possibly trigger popup or same-window captcha
                try:
                    driver.get(href)
                except WebDriverException:
                    try:
                        a = driver.find_element(By.XPATH, f"//a[contains(@href, '{href}')]")
                        a.click()
                    except Exception:
                        pass
                time.sleep(1.2)
            else:
                try:
                    if href:
                        try:
                            a = driver.find_element(By.XPATH, f"//a[contains(@href, \"{href}\")]")
                            a.click()
                        except Exception:
                            a = driver.find_element(By.XPATH, f"//a[@href=\"{href}\"]")
                            a.click()
                    else:
                        a = driver.find_element(By.LINK_TEXT, text)
                        a.click()
                except StaleElementReferenceException:
                    print("Stale element while trying to click candidate — skipping.")
                    continue
                except Exception as e:
                    print("Click attempt failed:", e)
                    continue

            time.sleep(1.0)

            # detect popup window
            handles = driver.window_handles
            new_handles = [h for h in handles if h != original_handle]
            if new_handles:
                popup_handle = new_handles[-1]
                print("Detected new window/popup; switching to it.")
                driver.switch_to.window(popup_handle)
                time.sleep(0.8)

                # try find captcha image in popup
                img = None
                try:
                    img = driver.find_element(By.ID, "captchaImage")
                except Exception:
                    try:
                        imgs = driver.find_elements(By.XPATH, "//img[contains(translate(@src,'CAPTCHA','captcha'),'captcha') or contains(@id,'captcha') or contains(@class,'captcha')]")
                        if imgs:
                            img = imgs[0]
                    except Exception:
                        img = None

                tmp = None
                if img:
                    tmp = os.path.join(tempfile.gettempdir(), f"doc_captcha_{int(time.time())}.png")
                    ok = _save_captcha_image_from_element(img, tmp)
                    if ok:
                        print("Document captcha image saved to:", tmp)
                    else:
                        print("Failed to save captcha image from popup; please type captcha manually in popup.")
                else:
                    print("No captcha image found in popup; if captcha is present, please type it in the popup.")

                if manual:
                    print("★ ACTION REQUIRED: Please type the captcha in the popup window and click the popup's SUBMIT/DOWNLOAD button.")
                    print("The script will wait (without refreshing the detail page) for you to finish.")
                    # Wait for popup to be closed or for PDF link to appear — do NOT refresh detail page while waiting
                    out = _poll_for_pdf_or_popup_close(driver, popup_handle, detail_url, timeout=captcha_poll_timeout, interval=1.0)
                    # ensure popup is closed to continue
                    try:
                        if popup_handle in driver.window_handles:
                            # attempt gentle close (user may not have closed it)
                            try:
                                driver.switch_to.window(popup_handle)
                                # do not try to click submit automatically
                                # just let user finish and close
                            except Exception:
                                pass
                    except Exception:
                        pass

                    if out:
                        return out
                    else:
                        print("Timed out waiting for manual captcha submission in popup for this candidate. Moving to next candidate.")
                        # if popup still open, attempt to close it (best effort) and switch back
                        try:
                            if popup_handle in driver.window_handles:
                                driver.switch_to.window(popup_handle)
                                try:
                                    driver.close()
                                except Exception:
                                    pass
                                # switch back
                                driver.switch_to.window(original_handle)
                        except Exception:
                            if driver.window_handles:
                                driver.switch_to.window(driver.window_handles[0])
                        time.sleep(0.6)
                        continue
                else:
                    raise RuntimeError("Auto-captcha not configured")

            else:
                # no popup — check for same-window captcha
                time.sleep(0.8)
                img = None
                try:
                    img = driver.find_element(By.ID, "captchaImage")
                except Exception:
                    try:
                        imgs = driver.find_elements(By.XPATH, "//img[contains(translate(@src,'CAPTCHA','captcha'),'captcha') or contains(@id,'captcha') or contains(@class,'captcha')]")
                        if imgs:
                            img = imgs[0]
                    except Exception:
                        img = None

                if img:
                    tmp = os.path.join(tempfile.gettempdir(), f"doc_captcha_{int(time.time())}.png")
                    ok = _save_captcha_image_from_element(img, tmp)
                    if ok:
                        print("Document captcha image saved to:", tmp)
                    else:
                        print("Could not save same-window captcha image; please type captcha in page.")

                    if manual:
                        print("★ ACTION REQUIRED: Please type the captcha into the page input and click Submit (on the page).")
                        out = _poll_for_pdf_after_manual_submit_same_window(driver, detail_url, timeout=captcha_poll_timeout, interval=1.0)
                        if out:
                            return out
                        else:
                            print("Timed out waiting for manual captcha submission in page for this candidate. Moving to next candidate.")
                            continue
                    else:
                        raise RuntimeError("Auto-captcha not configured")
                else:
                    # no captcha detected — try to find pdf links again
                    out = _find_pdf_on_page(driver)
                    if out:
                        return out

            # last-resort: perform a requests-based GET on current URL to see if it's a PDF
            try:
                s2 = cookies_to_session(driver)
                r = s2.get(driver.current_url, timeout=30, stream=True)
                if r.status_code == 200 and "pdf" in (r.headers.get("content-type") or "").lower():
                    fname = os.path.join(DOWNLOAD_DIR, f"tender_{int(time.time())}.pdf")
                    with open(fname, "wb") as f:
                        for chunk in r.iter_content(1024 * 8):
                            if chunk:
                                f.write(chunk)
                    return fname
            except Exception:
                pass

        except Exception as ex:
            print("Candidate failed:", ex)
            continue

    save_page_dump(driver, "page_no_success_after_candidates.html")
    raise RuntimeError("Tried all download candidates but couldn't get a PDF. Dumped page to page_no_success_after_candidates.html")
