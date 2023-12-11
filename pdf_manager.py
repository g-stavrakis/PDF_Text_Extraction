import os
import time
from typing import Any, List, Tuple

import PyPDF2
import pdfplumber
import pytesseract
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from rapidfuzz import fuzz
from pdf2image import convert_from_path
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextContainer, LTTextBoxHorizontal
from pdfminer.layout import LTFigure, LTRect
from pyprojroot import here


class TextElement:
    def __init__(self, text, bbox):
        self.text = text
        self.bbox = bbox

    def __eq__(self, other):
        if isinstance(other, TextElement):
            return self.text == other.text and self.is_position_similar(
                other.bbox
            )
        return False

    def __hash__(self):
        return hash((self.text, self.bbox))

    def is_position_similar(self, other_bbox):
        threshold = 100
        return all(
            abs(self_coord - other_coord) < threshold
            for self_coord, other_coord in zip(self.bbox, other_bbox)
        )


class PdfTableExtractor:
    @staticmethod
    def extract_table(
        pdf_path: str, page_num: int, table_num: int
    ) -> List[List[str]]:
        """
        Extracts a specific table from a specific page of a PDF file.

        This method uses pdfplumber to open the PDF and extract the table specified by
        the table number from the specified page.

        Args:
            pdf_path (str): The path to the PDF file.
            page_num (int): The page number from which to extract the table.
            table_num (int): The index of the table to be extracted on the specified page.

        Returns:
            List[List[str]]: A list of lists, where each sublist represents a row of the table.
        """
        with pdfplumber.open(pdf_path) as pdf:
            table_page = pdf.pages[page_num]
            table = table_page.extract_tables()[table_num]
        return table

    @staticmethod
    def table_converter(table: List[List[str]]) -> str:
        """
        Converts a table into a string representation with rows separated by newlines and
        columns separated by vertical bars.

        This method processes each cell of the table, replacing newline characters with spaces
        and handling None values, to create a clean, formatted string representation of the table.

        Args:
            table (List[List[str]]): The table to be converted, represented as a list of rows.

        Returns:
            str: A string representation of the table with formatted rows and columns.
        """
        table_string = ""
        for row in table:
            cleaned_row = [
                item.replace("\n", " ")
                if item is not None and "\n" in item
                else "None"
                if item is None
                else item
                for item in row
            ]
            table_string += "|" + "|".join(cleaned_row) + "|" + "\n"
        return table_string[:-1]


class PdfImageExtractor:
    @staticmethod
    def crop_image(element: Any, page_object: PdfReader.pages) -> None:
        """
        Crops an image element from a PDF page and saves it as a new PDF file.

        This method adjusts the media box of the page to the coordinates of the image element,
        effectively cropping the page to just the image. The cropped page is then saved as a new PDF.

        Args:
            element (Any): The image element to be cropped from the PDF.
            page_object (PdfReader.pages): The page object from which the image will be cropped.

        Returns:
            None. The cropped image is saved as 'cropped_image.pdf'.
        """
        [image_left, image_top, image_right, image_bottom] = [
            element.x0,
            element.y0,
            element.x1,
            element.y1,
        ]
        page_object.mediabox.lower_left = (image_left, image_bottom)
        page_object.mediabox.upper_right = (image_right, image_top)

        cropped_pdf_writer = PdfWriter()
        cropped_pdf_writer.add_page(page_object)

        with open("cropped_image.pdf", "wb") as cropped_pdf_file:
            cropped_pdf_writer.write(cropped_pdf_file)

    @staticmethod
    def convert_to_images(input_file: str) -> None:
        """
        Converts a PDF file to an image, saving the first page as a PNG file.

        This method uses pdf2image to convert the provided PDF file into a series of images.
        Currently, it only saves the first page of the PDF as an image.

        Args:
            input_file (str): The path to the PDF file to be converted.

        Returns:
            None. The first page of the PDF is saved as 'PDF_image.png'.
        """
        images = convert_from_path(input_file)
        image = images[0]
        output_file = "PDF_image.png"
        image.save(output_file, "PNG")

    @staticmethod
    def image_to_text(image_path: str) -> str:
        """
        Extracts text from an image file using Optical Character Recognition (OCR).

        This method uses pytesseract to perform OCR on the provided image and extract text.

        Args:
            image_path (str): The path to the image file from which text will be extracted.

        Returns:
            str: The text extracted from the image.
        """
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text


class PdfTextExtractor:
    @staticmethod
    def text_extraction(element: LTTextContainer) -> Tuple[str, List[any]]:
        """
        Extracts text and its formatting information from a text container element.

        This method goes through each text line and character in the given text container element
        (from a PDF document), extracting both the text content and the formatting details
        (like font name and size) for each character.

        Args:
            element (LTTextContainer): A text container element from a PDF document, typically
                                       containing text and associated formatting information.

        Returns:
            Tuple[str, List[any]]: A tuple where the first element is the extracted text as a string,
                                   and the second element is a list of unique formats (including font
                                   names and sizes) encountered in the text.
        """
        line_text = element.get_text()
        line_formats = []

        for text_line in element:
            if isinstance(text_line, LTTextContainer):
                for character in text_line:
                    if isinstance(character, LTChar):
                        line_formats.append(character.fontname)
                        line_formats.append(character.size)

        format_per_line = list(set(line_formats))
        return line_text, format_per_line


class PdfManager:
    def __init__(self, pdf_path: str):
        """
        Initializes the PdfManager with the path to the PDF document.

        This class manages the extraction of text, images, and tables from a PDF file,
        utilizing various extractor classes.

        Args:
            pdf_path (str): The file path to the PDF document to be processed.
        """
        self.pdf_path = pdf_path
        self.text_extractor = PdfTextExtractor()
        self.image_extractor = PdfImageExtractor()
        self.table_extractor = PdfTableExtractor()

    @staticmethod
    def remove_duplicated_text(
        page_content: List[str], similarity_threshold: int = 85
    ) -> List[str]:
        """
        Removes duplicated texts from a list of strings using fuzzy string matching.
        Texts are considered duplicates if their similarity score exceeds the specified threshold.

        Args:
            page_content (List[str]): The list of strings from which duplicates are to be removed.
            similarity_threshold (int): The threshold for fuzzy string similarity above which
                                        two strings are considered duplicates (default 85).

        Returns:
            List[str]: A list of strings with duplicates removed, based on fuzzy string matching.
        """
        unique_content = []
        for content in page_content:
            if not any(
                fuzz.token_set_ratio(content, other_content)
                > similarity_threshold
                for other_content in unique_content
            ):
                unique_content.append(content)
        return unique_content

    @staticmethod
    def process_text_element(
        element: LTTextContainer,
        page_text: List[str],
        line_format: List[str],
        page_content: List[str],
        table_extraction_flag: bool,
    ) -> None:
        """
        Processes a text element from a PDF page, extracting both the text and its formatting.

        Args:
            element (LTTextContainer): The text element to be processed.
            page_text (List[str]): Accumulator list for the text extracted from elements.
            line_format (List[str]): Accumulator list for the formatting of the extracted text.
            page_content (List[str]): Accumulator list for all content extracted from the page.
            table_extraction_flag (bool): Flag indicating if the extraction is currently within a table.

        Returns:
            None
        """
        if not table_extraction_flag:
            line_text, format_per_line = PdfTextExtractor.text_extraction(
                element
            )
            normalized_text = line_text.strip()
            page_text.append(normalized_text)
            line_format.append(format_per_line)
            page_content.append(normalized_text)

    @staticmethod
    def process_image_element(
        element: LTFigure,
        page_obj: Any,
        text_from_images: List[str],
        page_content: List[str],
        page_text: List[str],
        line_format: List[str],
    ) -> None:
        """
        Processes an image element from a PDF page, extracting any text contained within the image.

        Args:
            element (LTFigure): The image element to be processed.
            page_obj (Any): The page object from the PDF document.
            text_from_images (List[str]): Accumulator list for text extracted from images.
            page_content (List[str]): Accumulator list for all content extracted from the page.
            page_text (List[str]): Accumulator list for the text extracted from elements.
            line_format (List[str]): Accumulator list for the formatting of the extracted text.

        Returns:
            None
        """

        PdfImageExtractor.crop_image(element, page_obj)
        PdfImageExtractor.convert_to_images("cropped_image.pdf")
        image_text = PdfImageExtractor.image_to_text("PDF_image.png")
        text_from_images.append(image_text)
        page_content.append(image_text)
        page_text.append("image")
        line_format.append("image")

    def process_table_element(
        self,
        element: LTRect,
        pagenum: int,
        page: Any,
        tables: List[Any],
        table_num: int,
        text_from_tables: List[str],
        page_content: List[str],
        page_text: List[str],
        line_format: List[Any],
    ) -> Tuple[float, float]:
        """
        Processes a table element from a PDF page, extracting the table and converting it to text.

        Args:
            element (LTRect): The table element to be processed.
            pagenum (int): The current page number in the PDF document.
            page (Any): The page object from the PDF document.
            tables (List[Any]): List of table elements found on the current page.
            table_num (int): The index of the current table being processed.
            text_from_tables (List[str]): Accumulator list for text extracted from tables.
            page_content (List[str]): Accumulator list for all content extracted from the page.
            page_text (List[str]): Accumulator list for the text extracted from elements.
            line_format (List[Any]): Accumulator list for the formatting of the extracted text.

        Returns:
            Tuple[float, float]: The lower and upper bounds of the table element.
        """

        lower_side = page.bbox[3] - tables[table_num].bbox[3]
        upper_side = element.y1
        table = PdfTableExtractor.extract_table(
            self.pdf_path, pagenum, table_num
        )
        table_string = PdfTableExtractor.table_converter(table)
        text_from_tables.append(table_string)
        page_content.append(table_string)
        page_text.append("table")
        line_format.append("table")
        return lower_side, upper_side

    def cleanup(self) -> None:
        """
        Cleans up temporary files created during the PDF processing.

        This method removes any temporary image or cropped PDF files that were created
        during the extraction process.

        Returns:
            None
        """

        try:
            os.remove("cropped_image.pdf")
            os.remove("PDF_image.png")
        except FileNotFoundError:
            pass

    def process_pdf(self, page_number: int = None) -> str:
        """
        Processes the entire PDF document or a specific page, extracting text, images, and tables.

        This method goes through each page of the PDF (or a specific page if specified),
        extracting text, images, and tables, and returns the aggregated content.

        Args:
            page_number (int, optional): The specific page number to extract content from.
                                         If None, content from all pages is processed.

        Returns:
            str: Aggregated text content from the specified page(s) of the PDF.
        """

        pdf_reader = PyPDF2.PdfReader(self.pdf_path)
        text_per_page = {}

        for pagenum, page in enumerate(extract_pages(self.pdf_path)):
            page_obj = pdf_reader.pages[pagenum]
            (
                page_text,
                line_format,
                text_from_images,
                text_from_tables,
                page_content,
            ) = ([], [], [], [], [])
            table_num, first_element, table_extraction_flag = 0, True, False

            with pdfplumber.open(self.pdf_path) as pdf:
                page_tables = pdf.pages[pagenum]
                tables = page_tables.find_tables()

                page_elements = [
                    (element.y1, element) for element in page._objs
                ]
                page_elements.sort(key=lambda a: a[0], reverse=True)

                unique_text_elements = set()
                for i, (_, element) in enumerate(page_elements):
                    if isinstance(element, LTTextBoxHorizontal):
                        text_element = TextElement(
                            element.get_text(),
                            (element.x0, element.y0, element.x1, element.y1),
                        )
                        if text_element not in unique_text_elements:
                            unique_text_elements.add(text_element)
                            self.process_text_element(
                                element,
                                page_text,
                                line_format,
                                page_content,
                                table_extraction_flag,
                            )

                    if isinstance(element, LTFigure):
                        self.process_image_element(
                            element,
                            page_obj,
                            text_from_images,
                            page_content,
                            page_text,
                            line_format,
                        )

                    if isinstance(element, LTRect):
                        if first_element and (table_num + 1) <= len(tables):
                            (
                                lower_side,
                                upper_side,
                            ) = self.process_table_element(
                                element,
                                pagenum,
                                page,
                                tables,
                                table_num,
                                text_from_tables,
                                page_content,
                                page_text,
                                line_format,
                            )
                            table_extraction_flag = True
                            first_element = False
                        elif (
                            element.y0 >= lower_side
                            and element.y1 <= upper_side
                        ):
                            pass
                        elif not isinstance(page_elements[i + 1][1], LTRect):
                            table_extraction_flag = False
                            first_element = True
                            table_num += 1

                deduplicated_content = PdfManager.remove_duplicated_text(
                    page_content, similarity_threshold=75
                )
                text_per_page["Page_" + str(pagenum)] = [
                    page_text,
                    line_format,
                    text_from_images,
                    text_from_tables,
                    deduplicated_content,
                ]

        self.cleanup()

        if page_number is not None:
            return "".join(text_per_page.get(f"Page_{page_number}", [""])[4])
        else:
            return "".join(
                [
                    "".join(page_content[4])
                    for page_content in text_per_page.values()
                ]
            )


if __name__ == "__main__":
    # Example usage
    start_time = time.time()
    pdf_path = str(here("./Example PDF.pdf"))
    # pdf_path = str(here("./Example PDF.pdf"))
    pdf_path = "/Users/michael/Downloads/test_0009903AAJ2022092716483274.pdf"
    pdf_manager = PdfManager(pdf_path)
    result = pdf_manager.process_pdf()
    end_time = time.time()
    print(result)
    print("----------------------------------------")
    print("----------------------------------------")
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time} seconds")
    print("Done!")
