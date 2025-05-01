import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.firefox.options import Options


# Form Data
first_name = "Maram"
last_name = "Refeco"
c_code = "QA"
pnumber1 = "51093055"
email = "meroomg3@gmail.com"
ar_name = "مرام اسماعيل ينقمه ريفكو"
pnumber2 = "+97451093055"
card_num = "29973602777"



def initialize_driver():
    # Initialize Firefox webdriver
    options = Options()
    # Uncomment the line below if you want to run Firefox in headless mode
    # options.add_argument("--headless")

    # Disable loading images and CSS to improve efficiency
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("permissions.default.image", 2)  # Disable images
    firefox_profile.set_preference("permissions.default.stylesheet", 2)  # Disable CSS
    firefox_profile.set_preference(
        "dom.ipc.plugins.enabled.libflashplayer.so", "false"
    )  # Disable Flash
    options.profile = firefox_profile

    # Set page load strategy to 'eager' to not wait for all resources
    options.page_load_strategy = "eager"

    return webdriver.Firefox(options=options)


SUCCESS_SIGNAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appointment_success.txt")


def book_appointment(driver, url):
    """
    Attempt to book an appointment once.
    Returns: True if successful, False if failed
    """
    
    # Check if another instance has already succeeded
    if os.path.exists(SUCCESS_SIGNAL_FILE):
        print("Another bot instance has already booked an appointment. Terminating...")
        driver.quit()
        return True  # Return True to trigger termination

    try:
        driver.get(url)

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
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", element
                )
                element.send_keys(field["value"])
                print(f"Filled {field['id']} with {field['value']}")
            except Exception as field_error:
                print(f"Error filling {field['id']}: {field_error}")
                try:
                    xpath = f"//input[@id='{field['id']}'] | //div[@id='{field['id']}']"
                    fallback_element = driver.find_element(By.XPATH, xpath)
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        fallback_element,
                    )
                    driver.execute_script(
                        f"arguments[0].value = '{field['value']}';", fallback_element
                    )
                    driver.execute_script(
                        "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                        fallback_element,
                    )
                    print(f"Filled {field['id']} using fallback method")
                except Exception as e:
                    print(f"Both attempts to fill {field['id']} failed: {e}")

        # Special handling for phone input
        try:
            print("Handling phone input field...")
            country_select = driver.find_element(
                By.CSS_SELECTOR, "select.PhoneInputCountrySelect"
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", country_select
            )
            driver.execute_script(f"arguments[0].value = '{c_code}';", country_select)
            driver.execute_script(
                "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                country_select,
            )
            print("Selected country code")

            phone_input = driver.find_element(By.CSS_SELECTOR, "input.PhoneInputInput")
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", phone_input
            )
            phone_input.send_keys(pnumber1)
            print(f"Entered phone number: {pnumber1}")
        except Exception as phone_error:
            print(f"Error handling phone input: {phone_error}")
            try:
                print("Trying fallback method for phone input...")
                full_phone = driver.find_element(By.ID, "client[phone]")
                driver.execute_script(
                    "arguments[0].value = '+250 795 923 535';", full_phone
                )
                driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                    full_phone,
                )
                print("Set phone using fallback method")
            except Exception as e:
                print(f"Phone input fallback also failed: {e}")

        print("Filled out all form fields")

        # Check the checkbox
        try:
            checkbox = driver.find_element(By.NAME, "fields[field-15605500]")
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", checkbox
            )
            if not checkbox.is_selected():
                checkbox.click()
            print("Checkbox 'fields[field-15605500]' checked")
        except Exception as checkbox_error:
            print(f"Error checking the checkbox: {checkbox_error}")

        # Find and click the confirm appointment button
        confirm_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(., 'Confirm Appointment')]")
            )
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
            confirm_button,
        )
        driver.execute_script("arguments[0].click();", confirm_button)
        print("Clicked 'Confirm Appointment'")

        # Check for alert message about unavailable time
        try:
            alert_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//p[@role='alert']"))
            )
            alert_text = alert_element.text
            print(f"Alert detected: {alert_text}")
            return False  # Time slot not available
        except TimeoutException:
            # No alert found, which is good
            pass

        # Wait for confirmation page to ensure the appointment was booked
        try:
            wait.until(EC.url_contains("confirmation"))
            print("Success! Appointment booked!")

            # Take a screenshot of the confirmation
            driver.save_screenshot("appointment_confirmation.png")
            
            with open(SUCCESS_SIGNAL_FILE, "w") as f:
                f.write(f"Appointment booked successfully at: {time.ctime()}")
                
            return True  # Success
        except TimeoutException:
            # If we didn't get redirected to confirmation page, check again for alert
            try:
                alert_element = driver.find_element(By.XPATH, "//p[@role='alert']")
                print(f"Alert found after submission: {alert_element.text}")
                return False  # Failed
            except NoSuchElementException:
                # No alert but also no confirmation - general error
                print(
                    "No confirmation page and no alert detected. General error occurred."
                )
                return False  # Failed

    except Exception as e:
        print(f"Error during booking attempt: {e}")
        return False  # Failed


times = [
    ("11", "30"),
    ("11", "55"),
    ("12", "05"),
    ("12", "10"),
    ("12", "20"),
    ("12", "35"),
]

def getNext(month, day, hour, minute):
    # minute = int(minute)
    # hour = int(hour)
    # day = int(day)

    current_index = times.index((hour, minute))
    
    next_index = (current_index + 1) % len(times) 
    hour, minute = times[next_index]

    # minute = str(minute).zfill(2)
    # hour = str(hour).zfill(2)
    # day = str(day).zfill(2)

    return (month, day, hour, minute)


if __name__ == "__main__":
    # Get day, and month from command line arguments
    if len(sys.argv) >= 2:
        day = sys.argv[1]
    else:
        print("python oneDayBot.py <day>")
        sys.exit(1)
    hour = "11"
    minute = "55"
    # day = "27"
    month = "05"

    # Initialize the driver once outside the function
    driver = initialize_driver()

    try:
        max_retries = 10000
        retry_count = 0
        success = False
        # og_day = day

        while not success and retry_count < max_retries:
            retry_count += 1
            print(f"Attempt #{retry_count} to book appointment")

            # if int(day) > int(og_day) + 4:
            #     day = og_day
            # else:
            #     day = str(int(day) + 1).zfill(2)

            url = f"https://app.acuityscheduling.com/schedule/7cc5215a/appointment/63998238/calendar/6418639/datetime/2025-{month}-{day}T{hour}%3A{minute}%3A00%2B03%3A00"

            success = book_appointment(driver, url)

            if not success:
                print(
                    f"Booking failed. Retrying... (attempt {retry_count} of {max_retries})"
                )
                month, day, hour, minute = getNext(month, day, hour, minute)

        if success:
            print(f"Appointment successfully booked after {retry_count} attempt(s)!")
        else:
            print(f"Failed to book appointment after {max_retries} attempts.")

    except Exception as e:
        print(f"An error occurred outside the retry loop: {e}")
    finally:
        # Wait a moment before closing to see the final state
        time.sleep(5)
        # driver.quit()
