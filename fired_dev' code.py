import requests
import time
import csv
import random
import re
import os
import string
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from gologin import GoLogin
from selenium.webdriver.chrome.service import Service
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from dateutil import parser
import shutil
import json
from selenium.webdriver.common.action_chains import ActionChains

with open('root.txt', 'r') as file:
    root_data = [line.strip() for line in file]

if len(root_data) < 2:
    exit("Incomeplete Input")
landing_url = root_data[2].strip()

with open('user-agents.txt', 'r') as file:
    user_agents = [line.strip() for line in file] 

with open('api_key.txt', 'r') as file:
    API_KEY = file.read().strip()  # Read and remove any extra spaces or newlines

gologin = GoLogin({'token': API_KEY})

gl = None

def getRandTime():
    return random.randint(2,9)

def move_cursor_to_end(driver, element):
    # Execute a script to set the cursor position at the end
    element.send_keys(Keys.END)

def human_typing(driver, element, text, min_delay=0.1, max_delay=0.3):
    element.clear()
    for char in text:
        move_cursor_to_end(driver, element)  # Ensure the cursor is at the end
        element.send_keys(char)  # Send each character one by one
        time.sleep(random.uniform(min_delay, max_delay))

def extract_date_components(date_string):
    try:
        # Parse the date string using dateutil's parser
        parsed_date = parser.parse(date_string)

        day = f"{parsed_date.day:02d}"  # Format day with leading zero if necessary
        month = f"{parsed_date.month:02d}"  # Format month with leading zero if necessary
        year = str(parsed_date.year)  # Convert year to string

        return day, month, year
    except Exception as e:
        print(f"Error: {e}")
        return None

def clean_name(first_name, last_name):
    # Define a regex pattern to match special characters
    pattern = r'[^a-zA-Z\s]'  # Only allow letters and spaces

    # Remove special characters from first name and last name
    cleaned_first_name = re.sub(pattern, '', first_name)
    cleaned_last_name = re.sub(pattern, '', last_name)

    return cleaned_first_name, cleaned_last_name

def generate_password():
    return str(root_data[1].strip())

# Start the GoLogin profile
def start_gologin_profile():
    # Start the GoLogin profile and return the profile object
    profile = gl.start()
    return profile  # Return the WebSocket URL

# Create a Selenium WebDriver connected to the GoLogin profile
def create_gologin_driver(ws_url):
    chrome_options = Options()
    # Specify the path to your ChromeDriver
    chrome_driver_path = 'chromedriver.exe'  # Update this path
    # Set up the Chrome service
    service = Service(chrome_driver_path)

    # Set the remote debugging address to the GoLogin WebSocket URL
    chrome_options.add_experimental_option("debuggerAddress", ws_url)
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU usage (necessary for Windows)
    chrome_options.add_argument("--no-sandbox")  # Required for Linux to avoid sandboxing issues
    chrome_options.add_argument("--disable-dev-shm-usage")  # Avoid /dev/shm issues

    # Create a new Chrome driver instance
    driver = webdriver.Chrome(service=service,options=chrome_options)
    return driver


def read_excel(file_path):
    """Read the Excel file and return the DataFrame."""
    df = pd.read_csv(file_path)
    return df

def fill_form(driver,data):
    wait = WebDriverWait(driver, 10)  # Timeout after 10 seconds
    user_info = {}
    
    # Concatenate address fields
    user_info['address'] = ' '.join([str(data[key]) for key in ['House_Number','ad1', 'ad2', 'ad3', 'ad4', 'ad5','postcode'] if pd.notna(data[key])]).strip()
    # Determine gender from title
    title = data['title'].strip()
    user_info['gender'] = 'Male' if title == 'Mr' else 'Female'
    # Fill first name, last name, and other fields
    user_info['first_name'] = data['forename']
    user_info['last_name'] = data['surname']
    user_info['first_name'],user_info['last_name'] = clean_name(user_info['first_name'],user_info['last_name'])
    user_info['phone_number'] = str(data['Telephone'])
    user_info['email'] = data['email_address']

    # Parse date of birth
    day, month, year = extract_date_components(str(data['date_of_birth']))
    user_info['day'] = day
    user_info['month'] = month
    user_info['year'] = year
    
    # Fill the form fields
    # 1. Click on the gender radio button first (priority)
    gender_found = False
    while not gender_found:
        try:
            wait.until(EC.visibility_of_element_located((By.ID, "onetrust-accept-btn-handler"))).click()
        except:
            print("Cookies accepted")

        try:
            if user_info['gender'] == 'Male':
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'label[for="account_gender_male"]'))).click()
            else:
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'label[for="account_gender_female"]'))).click()
            gender_found = True
        except:
            print("Gender not found\n")
            driver.refresh()
            time.sleep(1)

    time.sleep(getRandTime())
    # 2. Enter first name and last name
    first_name =  wait.until(EC.visibility_of_element_located((By.NAME, "first_name")))
    #first_name.clear()
    human_typing(driver,first_name,user_info['first_name'])
    #first_name.send_keys(user_info['first_name'])
    
    time.sleep(getRandTime())

    last_name = wait.until(EC.visibility_of_element_located((By.NAME, "last_name")))
    #last_name.clear()
    human_typing(driver,last_name,user_info['last_name'])
    #last_name.send_keys(user_info['last_name'])

    time.sleep(getRandTime())

    # Country Code selector
    prefix_input = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'intl-tel-search-prefix')))
    if prefix_input.get_attribute('value') != "44":
        iti_arrow = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'iti-arrow')))
        iti_arrow.click()
        country_li = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'li.country.gg')))
        country_li.click()
        
    # 3. Enter phone number
    phone_number = wait.until(EC.visibility_of_element_located((By.NAME, "phone_number")))
    #phone_number.clear()
    human_typing(driver,phone_number,user_info['phone_number'])
    #phone_number.send_keys(user_info['phone_number'])
    
    time.sleep(getRandTime())

    # 4. Enter date
    day_element = wait.until(EC.visibility_of_element_located((By.NAME, "day"))) 
    day_select = Select(day_element)
    day_select.select_by_value(str(user_info['day']))  # Assuming month is passed as a number (1-12)

    time.sleep(getRandTime())

    # For the 'month'
    month_element = wait.until(EC.visibility_of_element_located((By.NAME, "month")))
    month_select = Select(month_element)
    month_select.select_by_value(str(user_info['month']))

    time.sleep(getRandTime())

    # year selection
    wait.until(EC.visibility_of_element_located((By.NAME, "year"))).send_keys(str(user_info['year']))

    time.sleep(getRandTime())

    # 5. Click on the 'Next' button (with class="regpath__button-next-text")
    next_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="regpath-button-next"]')))
    # Click the button
    next_button.click()
    # 5. Enter address
    address_found = False  
    while not address_found:
        try:
            address_search = wait.until(EC.visibility_of_element_located((By.ID, "address_search")))
            #address_search.clear()
            human_typing(driver,address_search,user_info['address'])
            #address_search.send_keys(user_info['address'])
            address_found = True 
            element = driver.find_element(By.ID, "address_search")
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            
        except Exception as e:
            time.sleep(2)  
    
    time.sleep(getRandTime())

          
    postcode_found = False  
    while not postcode_found:
        try:
            address_finder_div = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "regpath__address-finder-options-container")))
            # Wait for the first li with the class "address-option" to be visible
            first_address_option = WebDriverWait(address_finder_div, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "address-option"))
            )
            # Click on the first li element with the class "address-option"
            first_address_option.click()
            # Check if the postcode element is clickable
            postcode = wait.until(EC.element_to_be_clickable((By.ID, 'postcode')))
            postcode_found = True  # Exit the loop when postcode is found
            element = driver.find_element(By.ID, "postcode")
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
        
        except Exception as e:
            print(f"Error: Post Code not found\n {e} ")
            time.sleep(2) 
    
    # Wait for the outer span with class 'regpath__step active'
    next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="regpath-button-next"]')))
    # Click on the inner span
    next_btn.click()
    #######
    # 7. Enter email
    email = wait.until(EC.visibility_of_element_located((By.NAME, "email")))
    #email.clear()
    human_typing(driver,email,user_info['email'])
    #email.send_keys(user_info['email'])

    time.sleep(getRandTime())

    password = generate_password()
    print(password)
    # Wait for the password field to be visible and enter the password
    password_input = wait.until(EC.visibility_of_element_located((By.NAME, "password")))
    #password_input.clear()
    human_typing(driver,password_input,password)
    #password_input.send_keys(password)

    time.sleep(getRandTime())

    ########
    try:
        # Wait for the span with class "account-form__circle-symbol" containing text "GBP"
        gbp_span = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//span[@class='account-form__circle-symbol' and text()='GBP']"))
        )
        gbp_span.click()
    except Exception as e:
        print("GBP span not found, checking for the 3rd element instead.")
        
        try:
            # Find all elements with the specified class
            elements = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "account-form__circle-symbol"))
            )
            
            # Click the 3rd element
            if len(elements) >= 3:
                elements[2].click()
                
                # Now wait for the GBP span again
                gbp_span = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//span[@class='account-form__circle-symbol' and text()='GBP']"))
                )
                gbp_span.click()
                print("GBP span found, and clicked.")
            else:
                print("Less than 3 elements found with the class.")
        except Exception as e:
            print("An error occurred while processing:", e)

    ########
    # Wait for and click on the marketing opt-in checkbox
    marketing_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[@for='marketing_opt_in']")))
    driver.execute_script("arguments[0].scrollIntoView(true);", wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".regpath__marketing_opt_in"))))
    marketing_checkbox.click()

    time.sleep(getRandTime())

    # Wait for and click on the terms and privacy policy checkbox
    terms_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[@for='terms_privacy_policy']")))
    driver.execute_script("arguments[0].scrollIntoView(true);", wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".regpath__terms_privacy_policy"))))
    terms_checkbox.click()  
    
    time.sleep(getRandTime())

    # Wait for and click the submit button
    submit_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "account-form__submit-button")))
    driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
    submit_button.click()
    time.sleep(3)
    email_address = user_info['email']
    try:
        account_already_in_use = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "account-form__email-in-use"))) 
        password = "-1"
    except:
        print("Email address Not Exist Can be used")
    verification = "-1"
    try:
        element = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, "//h3[@class='bvs-msg-box__title' and text()='Verify Your Account']"))
        )
        verification = "CNV"
    except:
        verification = ""
        print("Verification Not required")

    driver.get("https://www.betvictor.com/logout")
    return email_address,password,verification

def email_exists(email, filename):
    """Check if the email already exists in the CSV file."""
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)  # Use DictReader for easier column access
            for row in reader:
                if row and row['email_address'].strip() == email:  # Check if email matches
                    return True
    except FileNotFoundError:
        print(f"File {filename} not found. Proceeding with processing.")
    return False

def delete_gologin_profile(profile_id):
    url = f'https://api.gologin.com/browser/{profile_id}'
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    # Make the DELETE request to the GoLogin API
    response = requests.delete(url, headers=headers)    
    if response.status_code == 200:
        print(f"Profile {profile_id} deleted successfully.\n")

def create_gologin_profile(proxy,index):
        profile_data = {
        "name": "Automations Profile " + str(index),
        "notes": "",  # Add any notes if needed
        "browserType": "chrome",  # Equivalent to your 'browser'
        "os": "win",  # Mapping 'os' to the provided format
        "startUrl": "",  # If you have any starting URL
        "googleServicesEnabled": False,
        "lockEnabled": False,
        "debugMode": False,
        "navigator": {
            "userAgent": random.choice(user_agents),  # You can provide a specific userAgent if needed
            "resolution": "1920x1080",  # Set resolution here
            "language": "en-US",  # Default language, update as necessary
            "platform": "Win32",  # Mapping Windows platform
            "doNotTrack": False,
            "hardwareConcurrency": 4,  # Number of CPU cores (modify as needed)
            "deviceMemory": 4,  # Amount of RAM (GB) (modify as needed)
            "maxTouchPoints": 0
        },
        "geoProxyInfo": {},
        "storage": {
            "local": True,
            "extensions": True,
            "bookmarks": True,
            "history": True,
            "passwords": True,
            "session": True
        },
        "proxyEnabled": True,
        "proxy": {
            "mode": "http",  # Mapping 'type' to 'mode'
            "host": proxy['host'],  # Mapping from your provided proxy data
            "port": int(proxy['port']),  # Converting port to an integer
            "username": proxy['username'],
            "password": proxy['password']
        },
        "dns": "",  # Provide if necessary
        "plugins": {
            "enableVulnerable": False,  # Adjust plugin settings as necessary
            "enableFlash": False
        },
        "timezone": {
            "enabled": True,
            "fillBasedOnIp": True,
            "timezone": "America/New_York"  # Adjust the timezone based on geo
        },
        "audioContext": {
            "mode": "off",
            "noise": 0
        },
        "canvas": {
            "mode": "off",
            "noise": 0
        },
        "fonts": {
            "families": [
                "Arial", "Verdana", "Helvetica"  # Add any specific fonts if necessary
            ],
            "enableMasking": True,
            "enableDomRect": True
        },
        "mediaDevices": {
            "videoInputs": 0,
            "audioInputs": 0,
            "audioOutputs": 0,
            "enableMasking": False
        },
        "webRTC": {
            "mode": "alerted",
            "enabled": True,
            "customize": True,
            "localIpMasking": False,
            "fillBasedOnIp": True,
            "publicIp": "",  # Provide if necessary
            "localIps": []
        },
        "webGL": {
            "mode": "noise",
            "getClientRectsNoise": 0,
            "noise": 0
        },
        "clientRects": {
            "mode": "noise",
            "noise": 0
        },
        "webGLMetadata": {
            "mode": "mask",
            "vendor": "",
            "renderer": ""
        },
        "webglParams": [],
        "profile": "",  # Provide if necessary
        "googleClientId": "",  # Provide if necessary
        "updateExtensions": True,
        "chromeExtensions": []}
        try:
            profile = gologin.create(profile_data)
            print("Profile created successfully:", profile)
            return profile
        except Exception as e:
            print(f"Error creating profile: {e}")
            return "-1"
            
def add_profile_to_folder(folder_name, profile_id):
    url = 'https://api.gologin.com/folders/folder'

    # Headers for the request
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    # Data payload for the PATCH request
    data = {
        "name": folder_name,  # Name of the folder
        "profiles": [profile_id],  # Profile ID(s) to be added
        "action": "add"
    }

    # Sending the PATCH request
    response = requests.patch(url, headers=headers, data=json.dumps(data))

    # Checking if the request was successful
    if response.status_code == 200:
        print(f"Profile {profile_id} added to folder '{folder_name}' successfully.")
    else:
        print(f"Failed to add profile to folder. Status Code: {response.status_code}, Response: {response.text}")

def read_proxies(file_path):
    proxies = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()  # Remove any leading/trailing whitespace
                if line:  # Check if the line is not empty
                    # Split the line by ':'
                    parts = line.split(':')
                    if len(parts) == 4:
                        # Create a dictionary for the proxy information
                        proxy = {
                            'host': parts[0],
                            'port': parts[1],
                            'username': parts[2],
                            'password': parts[3]
                        }
                        proxies.append(proxy)
                    else:
                        print(f"Invalid line format: {line}")
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return proxies


# read proxies list
file_path = 'iproyal-proxies.txt' 
proxies = read_proxies(file_path)

file_path = str(root_data[0].strip())+".csv"
df = read_excel(file_path)
with open('profile_ids.txt', 'r') as file:
    profile_ids = [line.strip() for line in file]

new_file_path = "output/"+file_path
file_exists = os.path.isfile(new_file_path)

for index, row in df.iterrows():
    if not email_exists(row['email_address'],"output/"+file_path) and row['postcode'].strip()[:2] != "BT":
        print("Processing....   "+str(row['email_address'])+"\n")
        proxy = proxies[index % len(proxies)]

        change_profile = False
        while not change_profile:
            profile_id_found = False
            while not profile_id_found:
                try:
                    PROFILE_ID = create_gologin_profile(proxy,index)
                    if PROFILE_ID!= "-1":
                        add_profile_to_folder("Betvictor",PROFILE_ID)
                        gl = GoLogin({'token': API_KEY,'profile_id': PROFILE_ID,})
                        ws_url = start_gologin_profile()
                        profile_id_found = True
                except:
                    print("Proxy Error \n")

            print("GoLogin browser started successfully.")
            print("WebSocket URL:", ws_url)
            driver = create_gologin_driver(ws_url)

            driver.get(landing_url)
            driver.get("https://www.betvictor.com/en-en/account/new?first_modal=true")
            if "Let's confirm you are human" in driver.page_source:
                gl.stop()
                if PROFILE_ID != "" and PROFILE_ID != "-1":
                    delete_gologin_profile(PROFILE_ID) 
                proxy = random.choice(proxies)
            else:
                change_profile = True        
    
        email,password,verification = fill_form(driver,row)
        
        # Create a new DataFrame with the current row data and additional columns
        new_row = row.copy()  # Create a copy of the current row
        new_row['Password'] = password  # Add the password
        new_row['Verification_status'] = verification  # Add verification status

        # Append the new row to the CSV file
        new_row_df = pd.DataFrame([new_row])  # Convert to DataFrame
        new_row_df.to_csv(new_file_path, mode='a', index=False, header=not file_exists)  # Append with header if file doesn't exist

        # Update the file_exists flag after writing the first row
        file_exists = True
        gl.stop()
        if PROFILE_ID != "" and PROFILE_ID != "-1":
            delete_gologin_profile(PROFILE_ID)
        time.sleep(10)



