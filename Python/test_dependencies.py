# Dependencies Installation Command
# pip install pyautogui pywinauto pyperclip requests pyotp selenium cryptography screeninfo pygetwindow google-api-python-client google-auth-httplib2 google-auth-oauthlib pypiwin32

import os
import time
import pyautogui
import pyperclip
import requests
import pyotp
import shutil
import smtplib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from screeninfo import get_monitors
from pywinauto.application import Application
from cryptography.fernet import Fernet
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def test_pyautogui():
    logging.info("Testing PyAutoGUI...")
    pyautogui.moveTo(100, 100, duration=0.5)
    logging.info("Mouse moved to (100, 100).")


def test_pyperclip():
    logging.info("Testing Pyperclip...")
    pyperclip.copy("Hello, Clipboard!")
    pasted_text = pyperclip.paste()
    logging.info(f"Copied to clipboard: {pasted_text}")


def test_requests():
    logging.info("Testing Requests...")
    response = requests.get("https://jsonplaceholder.typicode.com/posts/1")
    logging.info(f"Received response: {response.json()}")


def test_pyotp():
    logging.info("Testing PyOTP...")
    secret = pyotp.random_base32()
    otp = pyotp.TOTP(secret)
    logging.info(f"Generated OTP: {otp.now()}")


def test_selenium():
    logging.info("Testing Selenium...")
    driver = webdriver.Chrome()  # Ensure you have ChromeDriver set up
    driver.get("https://example.com")
    logging.info(f"Page title: {driver.title}")
    driver.quit()


def test_screeninfo():
    logging.info("Testing ScreenInfo...")
    monitors = get_monitors()
    for monitor in monitors:
        logging.info(f"Monitor: {monitor.name}, Resolution: {monitor.width}x{monitor.height}")


def test_pywinauto():
    logging.info("Testing PyWinAuto...")
    app = Application(backend="uia").start("notepad.exe")
    app.UntitledNotepad.edit.type_keys("Hello from PyWinAuto!", with_spaces=True)
    time.sleep(1)
    app.UntitledNotepad.menu_select("File->Exit")
    app.UntitledNotepad.DontSave.click()


def test_cryptography():
    logging.info("Testing Cryptography...")
    key = Fernet.generate_key()
    cipher = Fernet(key)
    encrypted = cipher.encrypt(b"Hello, Encryption!")
    decrypted = cipher.decrypt(encrypted)
    logging.info(f"Decrypted text: {decrypted.decode()}")


def test_google_api():
    logging.info("Testing Google API...")
    # Replace 'your_api_key_here' with a valid API key
    service = build("gmail", "v1", developerKey="your_api_key_here")
    logging.info("Google API Client successfully imported and initialized.")


def main():
    logging.info("Starting Dependency Test Script...")

    try:
        test_pyautogui()
        test_pyperclip()
        test_requests()
        test_pyotp()
        test_selenium()
        test_screeninfo()
        test_pywinauto()
        test_cryptography()
        test_google_api()
        logging.info("All tests completed successfully!")
    except Exception as e:
        logging.error(f"An error occurred during testing: {e}")


if __name__ == "__main__":
    main()
