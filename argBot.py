import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.firefox.options import Options


def book_appointment(url, first_name, last_name, c_code, pnumber1, email, ar_name, pnumber2, card_num, max_retries=10000):
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
        driver.get(url)
        retry_count = 0
        success = False
        
        while not success and retry_count < max_retries:
            try:
                retry_count += 1
                print(f"Attempt #{retry_count} to book appointment")
                
                wait = WebDriverWait(driver, 20)
                # Wait for the registration form to load
                wait.until(EC.presence_of_element_located((By.ID, "client[firstName]")))
                print("Registration form loaded")
                
                # Fill out the form with the provided details
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
                        element = driver.find_element(By.NAME, field["id"])
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        element.send_keys(field["value"])
                        print(f"Filled {field['id']} with {field['value']}")
                    except Exception as field_error:
                        print(f"Error filling {field['id']}: {field_error}")
                        try:
                            xpath = f"//input[@id='{field['id']}'] | //div[@id='{field['id']}']"
                            fallback_element = driver.find_element(By.XPATH, xpath)
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fallback_element)
                            driver.execute_script(f"arguments[0].value = '{field['value']}';", fallback_element)
                            driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", fallback_element)
                            print(f"Filled {field['id']} using fallback method")
                        except Exception as e:
                            print(f"Both attempts to fill {field['id']} failed: {e}")
                
                # Special handling for phone input
                try:
                    print("Handling phone input field...")
                    country_select = driver.find_element(By.CSS_SELECTOR, "select.PhoneInputCountrySelect")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", country_select)
                    driver.execute_script(f"arguments[0].value = '{c_code}';", country_select)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", country_select)
                    print("Selected country code")
                    
                    phone_input = driver.find_element(By.CSS_SELECTOR, "input.PhoneInputInput")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", phone_input)
                    phone_input.send_keys(pnumber1)
                    print(f"Entered phone number: {pnumber1}")
                except Exception as phone_error:
                    print(f"Error handling phone input: {phone_error}")
                    try:
                        print("Trying fallback method for phone input...")
                        full_phone = driver.find_element(By.ID, "client[phone]")
                        driver.execute_script("arguments[0].value = '+250 795 923 535';", full_phone)
                        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", full_phone)
                        print("Set phone using fallback method")
                    except Exception as e:
                        print(f"Phone input fallback also failed: {e}")
                
                print("Filled out all form fields")
                
                # Check the checkbox
                try:
                    checkbox = driver.find_element(By.NAME, "fields[field-15605500]")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                    if not checkbox.is_selected():
                        checkbox.click()
                    print("Checkbox 'fields[field-15605500]' checked")
                except Exception as checkbox_error:
                    print(f"Error checking the checkbox: {checkbox_error}")
                
                # Find and click the confirm appointment button
                confirm_button = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//button[contains(., 'Confirm Appointment')]")))
                
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", confirm_button)
                driver.execute_script("arguments[0].click();", confirm_button)
                print("Clicked 'Confirm Appointment'")
                
                # Check for alert message about unavailable time
                try:
                    alert_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//p[@role='alert']"))
                    )
                    alert_text = alert_element.text
                    print(f"Alert detected: {alert_text}")
                    driver.get(url)  # Refresh and try again
                    continue
                    if "no longer available" in alert_text.lower():
                        print("Time slot is no longer available. Retrying with page refresh...")
                except TimeoutException:
                    # No alert found, which is good
                    pass
                
                # Wait for confirmation page to ensure the appointment was booked
                try:
                    wait.until(EC.url_contains("confirmation"))
                    print(f"Success! Appointment booked after {retry_count} attempt(s)!")
                    
                    # Take a screenshot of the confirmation
                    driver.save_screenshot("appointment_confirmation.png")
                    success = True
                except TimeoutException:
                    # If we didn't get redirected to confirmation page, check again for alert
                    try:
                        alert_element = driver.find_element(By.XPATH, "//p[@role='alert']")
                        print(f"Alert found after submission: {alert_element.text}")
                        print("Retrying with page refresh...")
                        driver.get(url)
                    except NoSuchElementException:
                        # No alert but also no confirmation - general error
                        print("No confirmation page and no alert detected. General error occurred.")
                        driver.get(url)
                
            except TimeoutException as e:
                print(f"Timeout error: {e}")
                print(f"Retrying... (attempt {retry_count + 1} of {max_retries})")
                driver.get(url)  # Refresh and try again
            except Exception as e:
                print(f"Error during booking attempt: {e}")
                print(f"Retrying... (attempt {retry_count + 1} of {max_retries})")
                driver.get(url)  # Refresh and try again
        
        if not success:
            print(f"Failed to book appointment after {max_retries} attempts.")
        
    except Exception as e:
        print(f"An error occurred outside the retry loop: {e}")
    finally:
        # Wait a moment before closing to see the final state
        time.sleep(5)
        # driver.quit()



if __name__ == "__main__":
    # Get day, hour, and minute from command line arguments
    if len(sys.argv) >= 4:
        month = sys.argv[1]
        day = sys.argv[2]
        hour = sys.argv[3]
        minute = sys.argv[4]
        if (any([len(i) < 2 for i in [month, day, hour, minute]])):
            print("\nnumbers must be formatted correctly: ## \ne.g. 4 should be 04\n")
            sys.exit(1)
    else:
        # Default values if not provided
        print("Usage: python argBot.py <month> <day> <hour> <minute>")
        sys.exit(1)
        
    url = f"https://app.acuityscheduling.com/schedule/7cc5215a/appointment/63998238/calendar/6418639/datetime/2025-{month}-{day}T{hour}%3A{minute}%3A00%2B03%3A00"
    first_name = "Maram"
    last_name = "Refeco"
    c_code = "QA"
    pnumber1 = "51093055"
    email = "meroomg3@gmail.com"
    ar_name = "مرام اسماعيل ينقمه ريفكو"
    pnumber2 = "+97451093055"
    card_num = "29973602777"
    
    book_appointment(url, first_name, last_name, c_code, pnumber1, email, ar_name, pnumber2, card_num)


# <p role="alert" class="css-1cngu90">One or more selected times are no longer available</p>