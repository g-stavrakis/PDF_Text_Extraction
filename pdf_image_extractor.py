from typing import Any

import pytesseract
from PIL import Image
from PyPDF2 import PdfWriter, PdfReader
from pdf2image import convert_from_path


class PdfImageExtractor:
    def crop_image(self, element: Any, pageObj: PdfReader.pages) -> None:
        """
        Crops an image element from a PDF page.

        Args:
            element (Any): The image element to be cropped.
            pageObj (PdfReader.page): The PDF page object.

        Returns:
            None. Saves the cropped image as a PDF file.
        """
        [image_left, image_top, image_right, image_bottom] = [
            element.x0,
            element.y0,
            element.x1,
            element.y1,
        ]
        pageObj.mediabox.lower_left = (image_left, image_bottom)
        pageObj.mediabox.upper_right = (image_right, image_top)

        cropped_pdf_writer = PdfWriter()
        cropped_pdf_writer.add_page(pageObj)

        with open("cropped_image.pdf", "wb") as cropped_pdf_file:
            cropped_pdf_writer.write(cropped_pdf_file)

    def convert_to_images(self, input_file: str) -> None:
        """
        Converts a PDF file to images.

        Args:
            input_file (str): The path to the PDF file.

        Returns:
            None. Saves the first page as an image.
        """
        images = convert_from_path(input_file)
        image = images[0]
        output_file = "PDF_image.png"
        image.save(output_file, "PNG")

    def image_to_text(self, image_path: str) -> str:
        """
        Extracts text from an image using OCR.

        Args:
            image_path (str): The path to the image file.

        Returns:
            str: Extracted text from the image.
        """
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
