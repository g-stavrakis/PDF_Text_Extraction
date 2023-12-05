import os
import PyPDF2
import pdfplumber
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTFigure, LTRect
from typing import Tuple, List, Any, Dict
from pyprojroot import here

from pdf_image_extractor import PdfImageExtractor
from pdf_table_extractor import PdfTableExtractor
from pdf_text_extractor import PdfTextExtractor

class PdfManager:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text_extractor = PdfTextExtractor()
        self.image_extractor = PdfImageExtractor()
        self.table_extractor = PdfTableExtractor()

    def process_text_element(self, element: LTTextContainer, page_text: List[str], line_format: List[str], page_content: List[str], table_extraction_flag: bool) -> None:
        if not table_extraction_flag:
            line_text, format_per_line = self.text_extractor.text_extraction(element)
            page_text.append(line_text)
            line_format.append(format_per_line)
            page_content.append(line_text)

    def process_image_element(self, element: LTFigure, page_obj: Any, text_from_images: List[str], page_content: List[str], page_text: List[str], line_format: List[str]) -> None:
        self.image_extractor.crop_image(element, page_obj)
        self.image_extractor.convert_to_images('cropped_image.pdf')
        image_text = self.image_extractor.image_to_text('PDF_image.png')
        text_from_images.append(image_text)
        page_content.append(image_text)
        page_text.append('image')
        line_format.append('image')

    def process_table_element(self, element: LTRect, pagenum: int, page: Any, tables: List[Any], table_num: int, text_from_tables: List[str], page_content: List[str], page_text: List[str], line_format: List[Any]) -> Tuple[float, float]:
        lower_side = page.bbox[3] - tables[table_num].bbox[3]
        upper_side = element.y1
        table = self.table_extractor.extract_table(self.pdf_path, pagenum, table_num)
        table_string = self.table_extractor.table_converter(table)
        text_from_tables.append(table_string)
        page_content.append(table_string)
        page_text.append('table')
        line_format.append('table')
        return lower_side, upper_side

    def cleanup(self) -> None:
        """
        Cleans up temporary files created during the PDF processing.

        Args:
            None

        Returns:
            None
        """
        try:
            os.remove('cropped_image.pdf')
            os.remove('PDF_image.png')
        except FileNotFoundError:
            pass

    def process_pdf(self) -> Dict[str, List[List[str]]]:
        pdf_reader = PyPDF2.PdfReader(self.pdf_path)
        text_per_page = {}

        for pagenum, page in enumerate(extract_pages(self.pdf_path)):
            page_obj = pdf_reader.pages[pagenum]
            page_text, line_format, text_from_images, text_from_tables, page_content = [], [], [], [], []
            table_num, first_element, table_extraction_flag = 0, True, False

            with pdfplumber.open(self.pdf_path) as pdf:
                page_tables = pdf.pages[pagenum]
                tables = page_tables.find_tables()

                page_elements = [(element.y1, element) for element in page._objs]
                page_elements.sort(key=lambda a: a[0], reverse=True)

                for i, component in enumerate(page_elements):
                    _, element = component

                    if isinstance(element, LTTextContainer):
                        self.process_text_element(element, page_text, line_format, page_content, table_extraction_flag)

                    if isinstance(element, LTFigure):
                        self.process_image_element(element, page_obj, text_from_images, page_content, page_text,
                                                   line_format)

                    if isinstance(element, LTRect):
                        if first_element and (table_num + 1) <= len(tables):
                            lower_side, upper_side = self.process_table_element(element, pagenum, page, tables,
                                                                                table_num, text_from_tables,
                                                                                page_content, page_text, line_format)
                            table_extraction_flag = True
                            first_element = False
                        elif element.y0 >= lower_side and element.y1 <= upper_side:
                            pass
                        elif not isinstance(page_elements[i + 1][1], LTRect):
                            table_extraction_flag = False
                            first_element = True
                            table_num += 1

            text_per_page['Page_' + str(pagenum)] = [page_text, line_format, text_from_images, text_from_tables, page_content]

        self.cleanup()

        return text_per_page

if __name__ == "__main__":
    # Example usage
    pdf_path = str(here("./Example PDF.pdf"))
    pdf_manager = PdfManager(pdf_path)
    result = pdf_manager.process_pdf()
    print(''.join(result['Page_0'][4]))
