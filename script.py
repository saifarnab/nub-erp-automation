import csv
import os
import re
import time
from urllib.parse import urlparse, urlunparse

from selenium import webdriver
from selenium.common import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select


class NUB:
    def __init__(self):
        self.login_url = 'http://103.17.36.65:8088/NUBERP/authorise/login'
        self.marks_entry_url = 'http://103.17.36.65:8088/NUBERP/courseResult/marksEntry'
        self.username = ''
        self.password = ''
        self.semester = ''
        self.section = ''

    @staticmethod
    def config_driver() -> webdriver.Chrome:
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        # options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")  # Set resolution
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/114.0.0.0 Safari/537.36")

        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })

        return driver

    def login(self, driver):
        driver.get(self.login_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginPassword"))
        )
        time.sleep(1)
        driver.find_element(By.ID, "username").send_keys(self.username)
        driver.find_element(By.ID, "loginPassword").send_keys(self.password)
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)

    def select_semester_section(self, driver):

        driver.get(self.marks_entry_url)

        wait = WebDriverWait(driver, 10)

        # Select Semester
        semester = wait.until(EC.presence_of_element_located((By.ID, "semesterId")))
        Select(semester).select_by_visible_text(self.semester)
        time.sleep(1)

        # Select Section:
        course = wait.until(EC.presence_of_element_located((By.ID, "sectionId")))
        Select(course).select_by_visible_text(self.section)
        time.sleep(1)
        driver.find_element(By.ID, "loadStudents").click()

    @staticmethod
    def marks_entry(driver, data):
        wait = WebDriverWait(driver, 5)

        # Initial page load
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".marks-details tbody tr")
            )
        )

        fields_config = {
            "attendance": "input[name^='classAttendanceMarks']",
            "assessment": "input[name^='continuousAssessmentMarks']",
            "midterm": "input[name^='midTermMarks']",
            "final": "input[name^='finalMarks']",
        }

        for student_id, attendance, assessment, midterm, final in data:

            marks = {
                "attendance": attendance,
                "assessment": assessment,
                "midterm": midterm,
                "final": final,
            }

            for field_name, value in marks.items():
                # Wait for page/table after previous reload
                wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".marks-details tbody tr")
                    )
                )

                # Find the student's row AGAIN
                try:
                    row = wait.until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                f"//div[contains(@class,'marks-details')]"
                                f"//tbody/tr[td[normalize-space()='{student_id}']]"
                            )
                        )
                    )
                except TimeoutException:
                    print(f"Not Found: {student_id}")
                    continue

                # Find the input AGAIN
                field = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            fields_config[field_name]
                        )
                    )
                )

                # Make sure the input belongs to this student's row
                field = row.find_element(
                    By.CSS_SELECTOR,
                    fields_config[field_name]
                )

                # Scroll into view
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    field
                )

                # Clear existing value
                field.clear()

                # Enter new value
                field.send_keys(str(value))

                # Trigger change/blur if the website saves on change
                driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                    field
                )

                # Give the website time to save/reload
                time.sleep(2)

                # Wait until page is ready again
                wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".marks-details tbody tr")
                    )
                )

            print(f"Completed: {student_id}")

        time.sleep(2)
        save_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//input[@name='_action_saveMarks' and @value='Save Marks']")
            )
        )

        save_button.click()
        time.sleep(4)

    def run(self):
        print('----------------- SCRIPT STARTS -------------------')
        self.username = input('Username: ')
        self.password = input('Password: ')
        # self.semester = input('Semester [e.g: CSE 1102 - B]: ')
        # self.section = input('Course & Section [e.g: CSE 1102 - B ]: ')
        self.semester = 'Summer 2026'
        self.section = 'CSE 1112 - B'
        data = [
            [42230100383, 10, 18, 24, 0],
            [42250202570, 1, 0, -7, 0],
            [42250302942, 10, 14, 7, 0],
            [42250302997, 10, 19, 17, 0],
            [42260103109, 5, 7, 23, 0],
            [42260103121, 10, 19, 6, 0],
            [42260103122, 10, 19, 15, 0],
            [42260103123, 10, 13, 5, 0],
            [42260103126, 4, 7, 16, 0],
            [42260103127, 10, 19, 10, 0],
            [42260103128, 3, 0, 5, 0],
            [42260103129, 10, 16, 10, 0],
            [42260103131, 8, 12, 8, 0],
            [42260103133, 10, 16, 25, 0],
            [42260103134, 10, 11, 28, 0],
            [42260103135, 7, 9, 9, 0],
            [42260103136, 10, 20, 28, 0],
            [42260103137, 2, 0, -7, 0],
            [42260103138, 10, 16, 20, 0],
            [42260103139, 10, 14, 17, 0],
            [42260103140, 7, 14, 6, 0],
            [42260103141, 8, 17, 11, 0],
            [42260103142, 5, 6, -7, 0],
            [42260103143, 10, 20, 26, 0],
            [42260103145, 10, 18, 24, 0],
            [42260103146, 10, 15, 10, 0],
            [42260103147, 10, 15, 12, 0],
            [42260103150, 10, 20, 27, 0],
            [42260103151, 3, 0, 2, 0],
            [42260103153, 10, 12, 9, 0],
            [42260103155, 9, 19, 30, 0],
            [42260103156, 8, 15, 26, 0],
            [42260103157, 10, 13, 6, 0],
            [42260103206, 10, 18, 18, 0],
            [42260103211, 4, 4, 13, 0]
        ]
        driver = self.config_driver()
        self.login(driver)
        self.select_semester_section(driver)
        self.marks_entry(driver, data)

        print('----------------- SCRIPT ENDS -------------------')


NUB().run()
