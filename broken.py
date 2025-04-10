import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.firefox.options import Options

def book_appointment(url, first_name, last_name, c_code, pnumber1, email, ar_name, pnumber2, card_num):
    # Initialize Firefox webdriver
    options = Options()
    # Uncomment the line below if you want to run Firefox in headless mode
    # options.add_argument("--headless")
    
    # Disable loading images and CSS to improve efficiency
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference('permissions.default.image', 2)  # Disable images
    firefox_profile.set_preference('permissions.default.stylesheet', 2)  # Disable CSS
    firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')  # Disable Flash
    options.profile = firefox_profile
    
    # Set page load strategy to 'eager' to not wait for all resources
    options.page_load_strategy = 'eager'
    
    driver = webdriver.Firefox(options=options)
    
    try:
        # Navigate to the appointment calendar
        # url = "https://app.acuityscheduling.com/schedule/7cc5215a/appointment/63998238/calendar/6418639"

        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        # Wait for the registration form to load
        wait.until(EC.presence_of_element_located((By.ID, "client[firstName]")))
        print("Registration form loaded")
        
        # Fill out the form with the provided details - using original send_keys method for text inputs
        # First handle the normal text fields
        form_fields = [
            {"id": "client[firstName]", "value": first_name},
            {"id": "client[lastName]", "value": last_name},
            {"id": "client[email]", "value": f"{email},"},
            {"id": "fields[field-15605471]", "value": ar_name},
            {"id": "fields[field-15605472]", "value": pnumber2},
            {"id": "fields[field-15605499]", "value": card_num},
        ]
        
        for field in form_fields:
            try:
                # Find element and scroll it into view
                element = driver.find_element(By.NAME, field["id"])
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)
                
                # Use the original send_keys method for regular form fields
                # element.clear()
                
                element.send_keys(field["value"])
                
                # If this is the email field, press Enter after inputting
                print(f"Filled {field['id']} with {field['value']}")
                if field["id"] == "client[email]":
                    time.sleep(0.5)
                    
            except Exception as field_error:
                print(f"Error filling {field['id']}: {field_error}")
                
                # Fallback: try using XPath or different approach
                try:
                    # Try with XPath that might be more reliable
                    xpath = f"//input[@id='{field['id']}'] | //div[@id='{field['id']}']"
                    fallback_element = driver.find_element(By.XPATH, xpath)
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fallback_element)
                    time.sleep(0.5)
                    driver.execute_script(f"arguments[0].value = '{field['value']}';", fallback_element)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", fallback_element)
                    print(f"Filled {field['id']} using fallback method")
                except Exception as e:
                    print(f"Both attempts to fill {field['id']} failed: {e}")
        
        # Special handling for phone input which has a more complex structure
        try:
            print("Handling phone input field...")
            
            # First select the country
            
            
            country_select = driver.find_element(By.CSS_SELECTOR, "select.PhoneInputCountrySelect")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", country_select)
            time.sleep(0.5)
            
            # Select Rwanda using JavaScript
            driver.execute_script(f"arguments[0].value = '{c_code}';", country_select)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", country_select)
            print("Selected country code")
            
            # Now handle the phone number input
            phone_input = driver.find_element(By.CSS_SELECTOR, "input.PhoneInputInput")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", phone_input)
            time.sleep(0.5)

            
            phone_input.send_keys(pnumber1)
            print(f"Entered phone number: {pnumber1}")
            
        except Exception as phone_error:
            print(f"Error handling phone input: {phone_error}")
            # Fallback approach for phone input
            try:
                print("Trying fallback method for phone input...")
                # Try direct input with the full formatted number
                full_phone = driver.find_element(By.ID, "client[phone]")
                driver.execute_script("arguments[0].value = '+250 795 923 535';", full_phone)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", full_phone)
                print("Set phone using fallback method")
            except Exception as e:
                print(f"Phone input fallback also failed: {e}")
        
        print("Filled out all form fields")
        
        
        
        # Check the checkbox with the name attribute "fields[field-15605500]"
        try:
            checkbox = driver.find_element(By.NAME, "fields[field-15605500]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
            time.sleep(0.5)
            if not checkbox.is_selected():
                checkbox.click()
            print("Checkbox 'fields[field-15605500]' checked")
        except Exception as checkbox_error:
            print(f"Error checking the checkbox: {checkbox_error}")
        
        
        
        # Find and click the confirm appointment button
        confirm_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//button[contains(@class, 'btn css-62w11') and contains(., 'Confirm Appointment')]")))
        
        # Scroll the confirm button into view and click using JavaScript
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", confirm_button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", confirm_button)
        print("Clicked 'Confirm Appointment'")
        
        # Wait for confirmation page to ensure the appointment was booked
        wait.until(EC.url_contains("confirmation"))
        print("Appointment successfully booked!")
        
        # Take a screenshot of the confirmation
        driver.save_screenshot("appointment_confirmation.png")
        
    except TimeoutException as e:
        print(f"Timeout error: {e}")
    except NoSuchElementException as e:
        print(f"Element not found: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Wait a moment before closing to see the final state
        time.sleep(5)

if __name__ == "__main__":
    url = "https://app.acuityscheduling.com/schedule/7cc5215a/appointment/63998238/calendar/6418639/datetime/2025-04-09T10%3A50%3A00%2B02%3A00"
    first_name = "Maram"
    last_name = "Refeco"
    c_code = "QA"
    pnumber1 = "51093055"
    email = "meroomg3@gmail.com"
    ar_name = "مرام اسماعيل ينقمه ريفكو"
    pnumber2 = "+97451093055"
    card_num = "29973602777"
    
    book_appointment(url, first_name, last_name, c_code, pnumber1, email, ar_name, pnumber2, card_num)
