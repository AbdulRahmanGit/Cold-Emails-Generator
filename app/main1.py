import cv2
import pytesseract
import re
from PIL import Image

class UPIDetailsExtractor:
    def __init__(self):
        # Initialize sections for transaction details
        self.sections = {
            "Transaction Status": "",
            "Amount": "",
            "Date": "",
            "Time": "",
            "UPI ID": "",
            "Merchant ID": ""
        }

    def preprocess_image(self, image):
        """Preprocess the image to improve OCR accuracy"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
        _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)  # Binarization
        return thresh

    def extract_text_from_image(self, image_path):
        """Extract text from the image using Tesseract OCR"""
        # Load the image using OpenCV
        image = cv2.imread(image_path)

        # Preprocess the image for better OCR results
        processed_image = self.preprocess_image(image)

        # Use pytesseract to extract text from the processed image
        extracted_text = pytesseract.image_to_string(processed_image)
        return extracted_text

    def parse_upi_details(self, text):
        """Parse UPI transaction details using regular expressions"""
        # Extract transaction status (Success/Failed)
        status_match = re.search(r'(Success|Failed)', text, re.IGNORECASE)
        self.sections["Transaction Status"] = status_match.group(0) if status_match else "Unknown"

        # Extract amount (₹500.00)
        amount_match = re.search(r'₹\s?(\d+[\.,]?\d*)', text)
        self.sections["Amount"] = amount_match.group(0) if amount_match else "Unknown"

        # Extract date (e.g., 24-09-2024)
        date_match = re.search(r'(\d{2}-\d{2}-\d{4})', text)
        self.sections["Date"] = date_match.group(0) if date_match else "Unknown"

        # Extract time (e.g., 12:45 PM)
        time_match = re.search(r'(\d{1,2}:\d{2}\s?(?:AM|PM))', text, re.IGNORECASE)
        self.sections["Time"] = time_match.group(0) if time_match else "Unknown"

        # Extract UPI ID (generic UPI regex pattern)
        upi_id_match = re.search(r'\b[\w\.-]+@[a-zA-Z]+\b', text)
        self.sections["UPI ID"] = upi_id_match.group(0) if upi_id_match else "Unknown"

        return self.sections

    def extract_upi_details(self, image_path):
        """Main function to extract UPI details from an image"""
        text = self.extract_text_from_image(image_path)
        upi_details = self.parse_upi_details(text)
        return upi_details

# Example usage:
if __name__ == "__main__":
    image_path = "path_to_your_image.png"  # Replace with your UPI screenshot path
    extractor = UPIDetailsExtractor()
    upi_details = extractor.extract_upi_details(image_path)
    print(upi_details)
