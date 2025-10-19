# # scraper.py — minimal script to open site and list Anantnag tender links
# import time, os
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from selenium.webdriver.chrome.service import Service

# load_dotenv()
# CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "chromedriver")
# BASE_URL = "https://jktenders.gov.in/nicgep/app"

# def create_driver():
#     opts = Options()
#     # opts.add_argument("--headless=new")   # remove this for visible browser
#     opts.add_argument("--no-sandbox")
#     opts.add_argument("--disable-dev-shm-usage")
#     service = Service(CHROMEDRIVER_PATH)
#     driver = webdriver.Chrome(service=service, options=opts)
#     driver.set_page_load_timeout(30)
#     return driver

# def go_to_tenders_by_location(driver):
#     driver.get(BASE_URL)
#     time.sleep(1.5)
#     try:
#         driver.find_element(By.LINK_TEXT, "Tenders by Location").click()
#         time.sleep(1.2)
#     except Exception:
#         elems = driver.find_elements(By.XPATH, "//a[contains(text(),'Tenders by Location')]")
#         if elems:
#             elems[0].click(); time.sleep(1.2)

# def search_by_location_anantnag(driver, manual_captcha=True):
#     # try select box first
#     try:
#         selects = driver.find_elements(By.TAG_NAME, "select")
#         for sel in selects:
#             for opt in sel.find_elements(By.TAG_NAME, "option"):
#                 if "ANANTNAG" in opt.text.upper():
#                     opt.click()
#                     break
#     except:
#         pass

#     # try text input fallback
#     try:
#         input_elem = driver.find_element(By.XPATH, "//input[@type='text' and (contains(@name,'district') or contains(@id,'district'))]")
#         input_elem.clear()
#         input_elem.send_keys("ANANTNAG")
#     except:
#         pass

#     # handle captcha manually (saves image captcha_search.png)
#     # handle captcha manually (saves image captcha_search.png)
#     if manual_captcha:
#         try:
#             # prefer the specific id we inspected
#             img = driver.find_element(By.ID, "captchaImage")
#             src = img.get_attribute("src")

#             saved = False
#             if src and src.startswith("data:image"):
#                 # try decoding base64; if it fails, fallback to element screenshot
#                 try:
#                     import base64
#                     header, b64 = src.split(",", 1)
#                     img_bytes = base64.b64decode(b64)
#                     with open("captcha_search.png", "wb") as f:
#                         f.write(img_bytes)
#                     print("Captcha saved as captcha_search.png (decoded from base64). Open it and type the text.")
#                     saved = True
#                 except Exception as e:
#                     print("Base64 decode failed, will try element screenshot. Error:", e)

#             if not saved:
#                 # element screenshot fallback (works for data URI or normal images)
#                 try:
#                     img.screenshot("captcha_search.png")
#                     print("Captcha saved as captcha_search.png (element screenshot). Open it and type the text.")
#                     saved = True
#                 except Exception as e:
#                     # last resort: try downloading via requests if src is a URL
#                     print("Element screenshot failed:", e)
#                     if src and src.startswith("http"):
#                         try:
#                             import requests
#                             r = requests.get(src, timeout=15)
#                             with open("captcha_search.png", "wb") as f:
#                                 f.write(r.content)
#                             print("Captcha saved as captcha_search.png (download). Open it and type the text.")
#                             saved = True
#                         except Exception as e2:
#                             print("Download attempt failed:", e2)

#             if not saved:
#                 print("Could not save captcha image. You may need to enter captcha manually in browser.")
#                 # Let the user type captcha in browser manually; pause until Enter
#                 input("If you typed captcha manually on the page, press Enter here to continue...")

#             # prompt for captcha entry if using automated input
#             try:
#                 code = input("Enter captcha for SEARCH page (or press Enter if you typed it into the page): ").strip()
#             except Exception:
#                 code = ""

#             # robustly locate captcha input field and fill if we have a code
#             if code:
#                 input_selectors = [
#                     "//input[@type='text' and (contains(@name,'captcha') or contains(@id,'captcha'))]",
#                     "//input[@type='text' and (contains(@placeholder,'Captcha') or contains(@aria-label,'captcha'))]",
#                     "//input[@type='text']"
#                 ]
#                 inp = None
#                 for sel in input_selectors:
#                     try:
#                         cand = driver.find_element(By.XPATH, sel)
#                         if cand.is_displayed() and cand.is_enabled():
#                             inp = cand
#                             break
#                     except:
#                         continue
#                 if inp:
#                     inp.clear()
#                     inp.send_keys(code)
#                 else:
#                     print("Captcha input field not found — ensure you typed captcha manually on the page.")
#         except Exception as e:
#             print("Captcha handling raised an exception:", e)


#     # click search
#     try:
#         driver.find_element(By.XPATH, "//input[@type='submit' or @value='Go' or @value='Search']").click()
#     except:
#         try:
#             driver.find_element(By.XPATH, "//button[contains(text(),'Search') or contains(text(),'Go')]").click()
#         except:
#             pass

#     time.sleep(2)
#     # If a JS alert popped ("Please enter Captcha."), accept it so Selenium can continue.
#     try:
#         # Try to get page source; if an unexpected alert exists, handle it.
#         html = driver.page_source
#     except Exception as e:
#         # handle UnexpectedAlertPresentException by accepting the alert, then retry
#         try:
#             alert = driver.switch_to.alert
#             print("An alert was present with text:", alert.text)
#             # give you a moment to see/close it manually if you prefer
#             try:
#                 alert.accept()
#                 print("Alert accepted programmatically.")
#             except:
#                 print("Could not accept alert programmatically. Please close it manually and press Enter here.")
#                 input("Press Enter after you close the alert in the browser...")
#         except Exception as e2:
#             print("No alert accessible or failed to switch_to.alert:", e2)
#         # retry page source after handling alert
#         time.sleep(0.5)
#         html = driver.page_source

#     soup = BeautifulSoup(html, "html.parser")
#     links = []
#     for a in soup.find_all("a", href=True):
#         href = a['href']
#         if "FrontEndTenderDetails" in href or "FrontEndAdvancedSearchResult" in href or "component=FrontEndTenderDetails" in href:
#             full = href if href.startswith("http") else ("https://jktenders.gov.in" + href)
#             links.append(full)
#     # dedupe
#     seen = []
#     for l in links:
#         if l not in seen: seen.append(l)
#     return seen

# if __name__ == "__main__":
#     d = create_driver()
#     try:
#         go_to_tenders_by_location(d)
#         links = search_by_location_anantnag(d, manual_captcha=True)
#         print("Found", len(links), "tender links. Showing up to 10:")
#         for i,l in enumerate(links[:10],1):
#             print(i, l)
#     finally:
#         d.quit()

# scraper.py — minimal script to open site and list Anantnag tender links
import time, os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException

load_dotenv()
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "chromedriver")
BASE_URL = "https://jktenders.gov.in/nicgep/app"

def create_driver():
    opts = Options()
    # opts.add_argument("--headless=new")   # remove this for visible browser (useful for captcha)
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(30)
    return driver

def go_to_tenders_by_location(driver):
    driver.get(BASE_URL)
    time.sleep(1.5)
    try:
        driver.find_element(By.LINK_TEXT, "Tenders by Location").click()
        time.sleep(1.2)
    except Exception:
        elems = driver.find_elements(By.XPATH, "//a[contains(text(),'Tenders by Location')]")
        if elems:
            elems[0].click(); time.sleep(1.2)

def _save_captcha_image_if_present(driver):
    """Save captcha image to captcha_search.png (best-effort)."""
    try:
        img = None
        try:
            img = driver.find_element(By.ID, "captchaImage")
        except Exception:
            imgs = driver.find_elements(By.XPATH, "//img[contains(translate(@src,'CAPTCHA','captcha'),'captcha') or contains(@id,'captcha') or contains(@class,'captcha')]")
            if imgs:
                img = imgs[0]

        if not img:
            return False

        src = img.get_attribute("src") or ""
        saved = False
        if src.startswith("data:image"):
            try:
                import base64
                header, b64 = src.split(",", 1)
                # pad base64 safely
                b64 = b64 + "=="
                with open("captcha_search.png", "wb") as f:
                    f.write(base64.b64decode(b64))
                print("Captcha saved as captcha_search.png (decoded from base64). Open it and type the text in the browser page.")
                saved = True
            except Exception as e:
                print("Base64 decode failed, will try element screenshot. Error:", e)
        if not saved:
            try:
                img.screenshot("captcha_search.png")
                print("Captcha saved as captcha_search.png (element screenshot). Open it and type the text in the browser page.")
                saved = True
            except Exception as e:
                print("Element screenshot failed:", e)
        return saved
    except Exception as ex:
        print("Captcha save helper failed:", ex)
        return False

def search_by_location_anantnag(driver, manual_captcha=True):
    # try select box first
    try:
        selects = driver.find_elements(By.TAG_NAME, "select")
        for sel in selects:
            for opt in sel.find_elements(By.TAG_NAME, "option"):
                if "ANANTNAG" in opt.text.upper():
                    opt.click()
                    break
    except:
        pass

    # try text input fallback
    try:
        input_elem = driver.find_element(By.XPATH, "//input[@type='text' and (contains(@name,'district') or contains(@id,'district'))]")
        input_elem.clear()
        input_elem.send_keys("ANANTNAG")
    except:
        pass

    # Helper to save captcha image (best-effort)
    def _save_captcha():
        try:
            img = None
            try:
                img = driver.find_element(By.ID, "captchaImage")
            except Exception:
                imgs = driver.find_elements(By.XPATH, "//img[contains(translate(@src,'CAPTCHA','captcha'),'captcha') or contains(@id,'captcha') or contains(@class,'captcha')]")
                if imgs:
                    img = imgs[0]

            if not img:
                return False

            src = img.get_attribute("src") or ""
            saved = False
            if src.startswith("data:image"):
                try:
                    import base64
                    header, b64 = src.split(",", 1)
                    # safe-pad base64 then decode
                    b64 = b64 + "=="
                    with open("captcha_search.png", "wb") as f:
                        f.write(base64.b64decode(b64))
                    print("Captcha saved as captcha_search.png (decoded from base64).")
                    saved = True
                except Exception as e:
                    print("Base64 decode failed, will try element screenshot. Error:", e)

            if not saved:
                try:
                    img.screenshot("captcha_search.png")
                    print("Captcha saved as captcha_search.png (element screenshot).")
                    saved = True
                except Exception as e:
                    print("Element screenshot failed:", e)
            return saved
        except Exception as ex:
            print("Captcha save failed:", ex)
            return False

    if manual_captcha:
        _save_captcha()
        print("Manual captcha mode: please type captcha into the browser page input. The script will detect it and submit automatically.")

    # selectors to find the page captcha input (we look for value attribute)
    captcha_selectors = [
        "//input[@type='text' and (contains(@name,'captcha') or contains(@id,'captcha'))]",
        "//input[@type='text' and (contains(@placeholder,'Captcha') or contains(@aria-label,'captcha'))]",
        "//input[@type='text']"
    ]

    # submit button selectors to click once when captcha detected
    submit_selectors = [
        "//input[@type='submit' or @value='Go' or @value='Search']",
        "//button[contains(text(),'Search') or contains(text(),'Go')]"
    ]

    def click_submit_once():
        for xp in submit_selectors:
            try:
                elems = driver.find_elements(By.XPATH, xp)
                if elems:
                    elems[0].click()
                    return True
            except Exception:
                continue
        return False

    # DON'T click submit immediately — it will trigger the "Please enter Captcha." alert loop.
    # Instead, wait for the user to type the captcha into the page input, then auto-click once.

    timeout_total = 180  # seconds to wait for user to type captcha / results
    poll_interval = 0.7
    start = time.time()
    submitted = False
    links_found = []

    while time.time() - start < timeout_total:
        time.sleep(poll_interval)

        # 1) Check if results already present (page might have loaded from previous action)
        try:
            page_html = driver.page_source or ""
            if ("FrontEndTenderDetails" in page_html) or ("FrontEndAdvancedSearchResult" in page_html) or ("tenders documents" in page_html.lower()):
                # parse anchors
                soup = BeautifulSoup(page_html, "html.parser")
                anchors = soup.find_all("a", href=True)
                candidate_links = []
                for a in anchors:
                    href = a.get('href')
                    if href and ("FrontEndTenderDetails" in href or "FrontEndAdvancedSearchResult" in href or "component=FrontEndTenderDetails" in href):
                        full = href if href.startswith("http") else ("https://jktenders.gov.in" + href)
                        candidate_links.append(full)
                if candidate_links:
                    # dedupe preserving order
                    seen = []
                    for l in candidate_links:
                        if l not in seen:
                            seen.append(l)
                    links_found = seen
                    break
        except Exception:
            pass

        # 2) If user typed captcha into the input, detect value and click submit once
        if not submitted and manual_captcha:
            try:
                value_found = ""
                for sel in captcha_selectors:
                    try:
                        el = driver.find_element(By.XPATH, sel)
                        v = (el.get_attribute("value") or "").strip()
                        if v:
                            value_found = v
                            break
                    except Exception:
                        continue

                if value_found:
                    print("Detected captcha value entered in page input.")
                    # click submit once
                    ok = click_submit_once()
                    if not ok:
                        print("Could not find a Submit button to click; please click Submit yourself in the browser once.")
                    else:
                        print("Clicked Submit after captcha entry. Waiting for results...")
                    submitted = True
                    # accept any immediate alert (e.g. server may still show one); don't loop on it
                    try:
                        alert = driver.switch_to.alert
                        try:
                            _txt = alert.text
                        except Exception:
                            _txt = ""
                        try:
                            alert.accept()
                            print("Accepted alert after submit:", repr(_txt))
                        except Exception:
                            pass
                    except Exception:
                        pass
                    # continue waiting for results to appear
                    continue
            except Exception:
                pass

        # 3) accept any stray alert (but don't re-submit)
        try:
            try:
                alert = driver.switch_to.alert
                try:
                    atext = alert.text
                except Exception:
                    atext = ""
                try:
                    alert.accept()
                    print("Accepted unexpected alert during wait:", repr(atext))
                except Exception:
                    pass
            except Exception:
                # no alert present
                pass
        except Exception:
            pass

    # after waiting loop, attempt to parse anchors one last time
    try:
        html = driver.page_source or ""
        soup = BeautifulSoup(html, "html.parser")
        anchors = soup.find_all("a", href=True)
        candidate_links = []
        for a in anchors:
            href = a.get('href')
            if href and ("FrontEndTenderDetails" in href or "FrontEndAdvancedSearchResult" in href or "component=FrontEndTenderDetails" in href):
                full = href if href.startswith("http") else ("https://jktenders.gov.in" + href)
                candidate_links.append(full)
        seen = []
        for l in candidate_links:
            if l not in seen:
                seen.append(l)
        links_found = seen
    except Exception:
        links_found = []

    # dedupe final and return
    # dedupe final and filter common pagination/refresh helper links
    seen = []
    filtered_links = []
    for l in links_found:
        low = (l or "").lower()
        # skip table pagination, refresh helper links and obvious non-detail anchors
        if "tablepages.link" in low or "tablepages.linkpage" in low or "tablepages.linklast" in low or "tablepages.linkfwd" in low:
            continue
        if "afrontendadvancedsearchresult" in low and "table" in low:
            continue
        if "refresh" in low and "page" in low:
            continue
        if l not in seen:
            seen.append(l)
            filtered_links.append(l)

    return filtered_links


    def click_submit_once():
        for xp in submit_xpaths:
            try:
                btns = driver.find_elements(By.XPATH, xp)
                if btns:
                    btns[0].click()
                    return True
            except Exception:
                continue
        return False

    # initial submit attempt (user may not have typed captcha yet)
    try:
        click_submit_once()
    except UnexpectedAlertPresentException:
        # will handle below
        pass
    except Exception:
        pass

    # After clicking submit, the page often raises an alert "Please enter Captcha."
    # Accept the alert if present, then wait/poll for user to type captcha in the page and resubmit.
    try:
        # try to accept alert if present immediately
        try:
            alert = driver.switch_to.alert
            try:
                txt = alert.text
            except Exception:
                txt = ""
            print("Alert present after submit:", repr(txt))
            try:
                alert.accept()
                print("Alert accepted programmatically.")
            except Exception:
                print("Could not accept alert programmatically.")
        except NoAlertPresentException:
            pass
        except Exception:
            # sometimes switch_to.alert raises UnexpectedAlertPresentException which we already handled above
            pass
    except Exception:
        pass

    # Now wait for either:
    #  - results to appear (links in page)
    #  - OR user to type captcha in the captcha input field -> then auto-submit
    timeout_total = 180  # seconds to wait for user to type captcha
    start_time = time.time()
    links_found = []
    while time.time() - start_time < timeout_total:
        time.sleep(0.7)

        # 1) check if results are already present (links we want)
        try:
            html = driver.page_source
            if html and ("FrontEndTenderDetails" in html or "FrontEndAdvancedSearchResult" in html or "Tenders" in html.lower()):
                soup = BeautifulSoup(html, "html.parser")
                anchors = [a for a in soup.find_all("a", href=True)]
                candidate_links = []
                for a in anchors:
                    href = a.get('href')
                    if href and ("FrontEndTenderDetails" in href or "FrontEndAdvancedSearchResult" in href or "component=FrontEndTenderDetails" in href):
                        full = href if href.startswith("http") else ("https://jktenders.gov.in" + href)
                        candidate_links.append(full)
                if candidate_links:
                    # dedupe preserving order
                    seen = []
                    for l in candidate_links:
                        if l not in seen:
                            seen.append(l)
                    links_found = seen
                    break
        except Exception:
            pass

        # 2) if not found, check whether user entered captcha in page input
        try:
            found_value = ""
            for sel in captcha_selectors:
                try:
                    el = driver.find_element(By.XPATH, sel)
                    val = (el.get_attribute("value") or "").strip()
                    if val:
                        found_value = val
                        break
                except Exception:
                    continue
            if found_value:
                print("Detected captcha value entered in page input ->", found_value)
                # submit the form again
                clicked = click_submit_once()
                if clicked:
                    # small wait for results to load
                    time.sleep(1.2)
                    # accept any alert if server shows it
                    try:
                        alert2 = driver.switch_to.alert
                        print("Alert after re-submit:", getattr(alert2, "text", ""))
                        try:
                            alert2.accept()
                        except Exception:
                            pass
                    except Exception:
                        pass
                    # continue loop to let results appear
                    continue
        except Exception:
            pass

        # 3) as a fallback also accept any alert (some flows raise alert after we polled)
        try:
            try:
                alt = driver.switch_to.alert
                try:
                    _ = alt.text
                except Exception:
                    pass
                try:
                    alt.accept()
                    print("Accepted unexpected alert during wait.")
                except Exception:
                    pass
            except NoAlertPresentException:
                pass
            except Exception:
                pass
        except Exception:
            pass

    # finished waiting loop - either links_found or timed out
    if not links_found:
        # final attempt: parse current page for links anyway
        try:
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            anchors = soup.find_all("a", href=True)
            candidate_links = []
            for a in anchors:
                href = a.get('href')
                if href and ("FrontEndTenderDetails" in href or "FrontEndAdvancedSearchResult" in href or "component=FrontEndTenderDetails" in href):
                    full = href if href.startswith("http") else ("https://jktenders.gov.in" + href)
                    candidate_links.append(full)
            seen = []
            for l in candidate_links:
                if l not in seen:
                    seen.append(l)
            links_found = seen
        except Exception:
            links_found = []

    # dedupe final
    seen = []
    links = []
    for l in links_found:
        if l not in seen:
            seen.append(l)
            links.append(l)

    return links

if __name__ == "__main__":
    d = create_driver()
    try:
        go_to_tenders_by_location(d)
        links = search_by_location_anantnag(d, manual_captcha=True)
        print("Found", len(links), "tender links. Showing up to 10:")
        for i,l in enumerate(links[:10],1):
            print(i, l)
    finally:
        d.quit()
