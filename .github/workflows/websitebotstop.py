import psutil
import os
import sys
os.system("pkill -9 chrome")  # Forcefully kill all Chrome processes
def kill_chrome():
    for process in psutil.process_iter(attrs=["pid", "name"]):
        if "chrome" in process.info["name"].lower():
            try:
                p = psutil.Process(process.info["pid"])
                p.terminate()  # Terminate gracefully
            except psutil.NoSuchProcess:
                pass  # Process already closed

kill_chrome()

#requiredlib = [selenium,time]
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.firefox.options import Options
#from selenium.webdriver.firefox.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
#import tempfile
#import uuid

'''
os.environ["MOZ_LOG"] = "debug"  # Enable verbose logging
# Initialize WebDriver
options = Options()
service = Service(excecutable_path="/usr/local/bin/geckodriver")
options.binary_location = '/usr/bin/firefox'
options.add_argument("--headless")
driver = webdriver.Firefox(options=options, service=service)
'''
# Chrome Options
options = Options()
# Use persistent user profile
USER_DATA_DIR = "/tmp/seedloaf-session"
options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
options.add_argument("--profile-directory=Default")  # Optional

options.binary_location = "/opt/chrome/chrome"
options.add_argument("--headless=new")  # Use new headless mode
options.add_argument("window-size=1920x1080")  # Ensure full viewport
options.add_argument("--disable-gpu")  # Fix rendering issues in headless
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
#temp_dir = f"/tmp/chrome-user-data-{uuid.uuid4()}"
#options.add_argument(f"--user-data-dir={temp_dir}")

# Bypass detection
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--enable-javascript")
options.add_argument("--disable-web-security")
service = Service("/usr/local/bin/chromedriver")  # Path to ChromeDriver
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-features=IsolateOrigins,site-per-process")
options.add_argument("--disable-extensions")

# Initialize WebDriver
driver = webdriver.Chrome(options=options,service=service) 
driver.get("https://accounts.seedloaf.com/sign-in")
#driver.maximize_window()

# Wait for page to fully load
WebDriverWait(driver, 10).until(lambda driver: driver.execute_script("return document.readyState") == "complete")

# Login flow function
def run_loginflow(usernamesec,passwordsec):
#---------------------------
    try:
        # Wait for the username field to be visible
        username = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "identifier-field"))
        )
        print("After waiting for username:\n"+driver.current_url)
        
        driver.execute_script("arguments[0].scrollIntoView(true);", username)
        driver.execute_script("arguments[0].click();", username)
        username.send_keys(usernamesec)
        username.send_keys(Keys.RETURN)
        
        # Optional: Wait to observe behavior (debugging)
        time.sleep(5)
        print("entered username")
        ran_loginflow = 1
    except Exception as e:
        print(f"Error occurred(username): {e}")
        print("After waiting for username:\n"+driver.current_url)
        
    #---------------------------
    
    try:
        try: # Check if username is incorrect
            wait = WebDriverWait(driver, 5)
            error_elem = wait.until(EC.visibility_of_element_located((By.ID, "error-identifier")))
            if error_elem:
                print("Username is incorrect")
                driver.quit()
                sys.exit()  
        except Exception as e:
            pass
            
        # Wait for the password field to be visible
        wait = WebDriverWait(driver, 15)
        password = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "password-field"))
        )
        print("After waiting for password:\n"+driver.current_url)
        
        # Now enter password  
        global old_url
        old_url = driver.current_url
        driver.execute_script("arguments[0].scrollIntoView(true);", password)
        driver.execute_script("arguments[0].click();", password)
        password.send_keys(passwordsec)
        password.send_keys(Keys.RETURN)
        # Optional: Wait to observe behavior (debugging)
        time.sleep(8)
        print("entered password")
    except Exception as e:
        print(f"Error occurred(password): {e}")
        print("After waiting for password:\n"+driver.current_url)
    ran_loginflow = 2



# Cleanup old marker
MARKER_FILE = "/tmp/seedloaf-session/.valid_session"
SESSION_DIR = "/tmp/seedloaf-session"
try:
    os.remove(MARKER_FILE)
except FileNotFoundError:
    pass
    
# Check dashboard
try:
    WebDriverWait(driver, 10).until(
        lambda d: "dashboard" in d.current_url
    )
    print("✅ Already logged in, at dashboard")
    ran_loginflow = 0
except:
    print("🔐 Not logged in — need to re-run login flow:\n"+driver.current_url)
    try: 
        ran_loginflow = 0
        usernamesec = os.getenv("USERNAME")
        passwordsec = os.getenv("PASSWORD")
        run_loginflow(usernamesec,passwordsec)
    except Exception as e:
        print("something wrong with secrets")
    # Write that Llogin flow has occured
    with open(MARKER_FILE, "w") as f:
        f.write("session valid")
    

#---------------------------
# Force-jump to the dashboard (post-login redirect can land elsewhere)
driver.get("https://seedloaf.com/dashboard")
time.sleep(6)
print("NOW AT:", driver.current_url)

def dump_debug():
    try:
        driver.get_screenshot_as_file("debug_stop.png")
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("DEBUG PAGE URL:", driver.current_url)
        print("ALL BUTTONS:")
        for b in driver.find_elements(By.TAG_NAME, "button"):
            print("  -", (b.text or "?").strip()[:60], "| ab:", (b.get_attribute("aria-label") or "")[:40], "| cls:", (b.get_attribute("class") or "")[:90])
        print("PAGE TEXT (first 1500 chars):")
        print(driver.find_element(By.TAG_NAME, "body").text[:1500])
    except Exception as e:
        print("debug dump error:", e)

#---------------------------
try:
    # Wait for the stop button to be present AND clickable (not disabled)
    try:
        time.sleep(5)  # let React hydrate the card
        wait = WebDriverWait(driver, 20)
        stopworld = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-error') and contains(@class, 'join-item') and not(@disabled)]"))
        )
        print("After waiting for stop:\n"+driver.current_url)
    except:
        try: # Check if password is incorrect, world already stopped, or still starting
            if  ran_loginflow and driver.current_url == old_url:
                error_elem = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "error-password")))
                if error_elem:
                    print("Password is incorrect")
                    driver.quit()
                    sys.exit()
            else:
                try:
                    body_text = driver.find_element(By.TAG_NAME, "body").text
                    if "Starting" in body_text:
                        print("World is still starting - stop again in a minute.")
                        dump_debug()
                        driver.quit()
                        sys.exit()
                    startworld = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Start World' or normalize-space()='Unarchive']")))
                    print("Start button found - world already stopped.")
                    driver.quit()
                    sys.exit()
                except Exception as e:
                    print(f"Neither Start nor Stop button found. Something might be wrong: {e}")
                    dump_debug()
                    driver.quit()
                    exit()
        except Exception as inner_exc:
            print(f"Unexpected error during start/stop button checks: {inner_exc}")
            print("After waiting for start/stop:\n"+driver.current_url)
            dump_debug()
            driver.quit()
            sys.exit()
    # Native click, JS fallback
    driver.execute_script("arguments[0].scrollIntoView(true);", stopworld)
    try:
        stopworld.click()
        print("Clicked stop (native)")
    except Exception:
        driver.execute_script("arguments[0].click();", stopworld)
        print("Clicked stop (js fallback)")
    time.sleep(2)
    # The stop click opens a confirm dialog with a "Force stop" button — click it
    try:
        forcestop = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Force stop']"))
        )
        try:
            forcestop.click()
            print("Clicked force stop (native)")
        except Exception:
            driver.execute_script("arguments[0].click();", forcestop)
            print("Clicked force stop (js fallback)")
    except Exception as e:
        print(f"No Force stop modal: {e}")
        dump_debug()
    time.sleep(2)
    for i in range(6):
        time.sleep(5)
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            print(f"+{(i+1)*5}s STATE:", " | ".join(body_text.split("\n")[:14])[:400])
        except Exception as e:
            print("state read error:", e)

except Exception as e:
    print(f"Error occurred(stop): {e}")



#---------------------------
''' #--- Jasper removed this feature now (only the start success alert maybe)
    #--- Uncomment to view any error alert if ur workflow doesnt work
try:
    # Wait for the alert div to appear
    alert_div = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//div[@role='alert']/div[2]"))
    )
    
    # Extract the text
    alert_text = alert_div.text
    print(f"{alert_text}")

except Exception as e:
    print(f"Error while fetching alert text: {e}")

#---------------------------
# Handle alert if present
try:
    alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
    alert_text = alert.text
    print(f"Alert text: {alert_text}")
    alert.accept()  # Accept the alert
except Exception:
    print("No alert found.")
    
# Check browser logs to see if any errors are happening
for entry in driver.get_log('browser'):
    print(entry)
'''

# Final debug dump before quitting
dump_debug()
driver.quit()
