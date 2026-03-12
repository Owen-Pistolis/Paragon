import pyautogui
import pytesseract
import cv2
import numpy as np
from PIL import Image
import time
import logging
from typing import Optional, Tuple, Union
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def take_screenshot(region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
    """Take a screenshot of the specified region or full screen"""
    try:
        # Add a small delay to ensure the screen has updated
        time.sleep(0.2)
        screenshot = pyautogui.screenshot(region=region)
        return screenshot
    except Exception as e:
        logger.error(f"Failed to take screenshot: {str(e)}")
        raise

def preprocess_image(image: Image.Image) -> np.ndarray:
    """Preprocess image for better OCR results"""
    try:
        # Convert to numpy array
        img_np = np.array(image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        # Apply thresholding to get black and white image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Noise removal
        denoised = cv2.fastNlMeansDenoising(binary)
        
        # Apply additional preprocessing for better text detection
        kernel = np.ones((1, 1), np.uint8)
        dilated = cv2.dilate(denoised, kernel, iterations=1)
        eroded = cv2.erode(dilated, kernel, iterations=1)
        
        return eroded
    except Exception as e:
        logger.error(f"Failed to preprocess image: {str(e)}")
        raise

def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    # Remove extra whitespace and convert to lowercase
    normalized = ' '.join(text.lower().split())
    # Remove punctuation except apostrophes
    normalized = re.sub(r'[^\w\s\']', '', normalized)
    return normalized

def find_text_on_screen(text: str, region: Optional[Tuple[int, int, int, int]] = None, timeout: int = 10, confidence: float = 0.7) -> bool:
    """
    Find text on screen using OCR with improved accuracy
    """
    try:
        normalized_search_text = normalize_text(text)
        logger.debug(f"Searching for normalized text: {normalized_search_text}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Take screenshot
            screenshot = take_screenshot(region)
            
            # Preprocess image
            processed_img = preprocess_image(screenshot)
            
            # Perform OCR with custom configuration
            config = '--psm 11 --oem 3'  # Page segmentation mode: Sparse text, OEM: Default
            screen_text = pytesseract.image_to_string(processed_img, config=config)
            normalized_screen_text = normalize_text(screen_text)
            logger.debug(f"OCR Result (normalized): {normalized_screen_text}")
            
            # Check if text is found (normalized comparison)
            if normalized_search_text in normalized_screen_text:
                logger.info(f"Text found: {text}")
                return True
                
            # Small delay before next attempt
            time.sleep(0.5)
            
        logger.warning(f"Text not found after {timeout} seconds: {text}")
        return False
        
    except Exception as e:
        logger.error(f"Error in find_text_on_screen: {str(e)}")
        return False

def get_text_location(image: np.ndarray, text: str, confidence_threshold: float = 0.6) -> Optional[Tuple[int, int, int, int]]:
    """
    Get the location of text in the image using OCR with improved accuracy
    """
    try:
        normalized_search_text = normalize_text(text)
        
        # Get detailed OCR data with custom configuration
        config = '--psm 11 --oem 3'
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=config)
        
        # Search for text (normalized comparison)
        best_match = None
        highest_confidence = -1
        
        for i, word in enumerate(data['text']):
            normalized_word = normalize_text(word)
            if normalized_search_text in normalized_word:
                confidence = float(data['conf'][i])
                if confidence > confidence_threshold and confidence > highest_confidence:
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    highest_confidence = confidence
                    best_match = (x, y, w, h)
                    
        if best_match:
            logger.debug(f"Found text with confidence {highest_confidence}")
            return best_match
                
        return None
        
    except Exception as e:
        logger.error(f"Error in get_text_location: {str(e)}")
        return None

def click_text_on_screen(text: str, region: Optional[Tuple[int, int, int, int]] = None, timeout: int = 10, confidence: float = 0.7) -> bool:
    """
    Click on text found on screen using OCR with improved accuracy
    """
    try:
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Take screenshot
            screenshot = take_screenshot(region)
            
            # Preprocess image
            processed_img = preprocess_image(screenshot)
            
            # Get text location
            location = get_text_location(processed_img, text, confidence)
            
            if location:
                x, y, w, h = location
                
                # Calculate center point
                center_x = x + w // 2
                center_y = y + h // 2
                
                # Adjust coordinates if region was specified
                if region:
                    center_x += region[0]
                    center_y += region[1]
                
                # Move mouse and click with smoother movement
                logger.debug(f"Moving mouse to ({center_x}, {center_y})")
                pyautogui.moveTo(center_x, center_y, duration=0.5)
                time.sleep(0.2)  # Small pause before clicking
                pyautogui.click(center_x, center_y)
                time.sleep(0.2)  # Small pause after clicking
                
                logger.info(f"Clicked text: {text}")
                return True
                
            # Small delay before next attempt
            time.sleep(0.5)
            
        logger.warning(f"Failed to click text after {timeout} seconds: {text}")
        return False
        
    except Exception as e:
        logger.error(f"Error in click_text_on_screen: {str(e)}")
        return False

def verify_element_visible(text: str, region: Optional[Tuple[int, int, int, int]] = None, timeout: int = 10, confidence: float = 0.7) -> bool:
    """
    Verify if an element with specific text is visible on screen
    """
    return find_text_on_screen(text, region, timeout, confidence)

def wait_for_text_visible(text: str, region: Optional[Tuple[int, int, int, int]] = None, timeout: int = 10, confidence: float = 0.7) -> bool:
    """
    Wait for text to become visible on screen
    """
    return verify_element_visible(text, region, timeout, confidence)

def advanced_image_search(template_path: str, region: Optional[Tuple[int, int, int, int]] = None, method: int = cv2.TM_CCOEFF_NORMED, threshold: float = 0.8) -> Optional[Tuple[int, int]]:
    """
    Use OpenCV for advanced template matching
    """
    try:
        # Take screenshot
        screenshot = take_screenshot(region)
        screenshot_np = np.array(screenshot)
        
        # Load template
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        
        # Convert both to same color space
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        # Perform template matching
        result = cv2.matchTemplate(screenshot_bgr, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            # Get template dimensions
            h, w = template.shape[:2]
            
            # Calculate center point
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            
            # Adjust coordinates if region was specified
            if region:
                center_x += region[0]
                center_y += region[1]
                
            logger.info(f"Template matched at ({center_x}, {center_y}) with confidence {max_val}")
            return (center_x, center_y)
            
        logger.warning(f"Template not found with confidence >= {threshold}")
        return None
        
    except Exception as e:
        logger.error(f"Error in advanced_image_search: {str(e)}")
        return None
