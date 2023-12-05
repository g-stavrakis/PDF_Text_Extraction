import os
import PyPDF2
import pdfplumber
from pyprojroot import here
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTFigure, LTRect

from pdf_image_extractor import PdfImageExtractor
from pdf_table_extractor import PdfTableExtractor
from pdf_text_extractor import PdfTextExtractor


# Assuming PdfTextExtractor, PdfImageExtractor, and PdfTableExtractor classes are defined as previously discussed

def process_pdf(pdf_path: str):
    # Initialize the extractor classes
    text_extractor = PdfTextExtractor()
    image_extractor = PdfImageExtractor()
    table_extractor = PdfTableExtractor()

    # Create a PDF reader object
    pdf_reader = PyPDF2.PdfReader(pdf_path)

    text_per_page = {}
    for pagenum, page in enumerate(extract_pages(pdf_path)):
        page_obj = pdf_reader.pages[pagenum]
        page_text, line_format, text_from_images, text_from_tables, page_content = [], [], [], [], []
        table_num, first_element, table_extraction_flag = 0, True, False

        with pdfplumber.open(pdf_path) as pdf:
            page_tables = pdf.pages[pagenum]
            tables = page_tables.find_tables()

            page_elements = [(element.y1, element) for element in page._objs]
            page_elements.sort(key=lambda a: a[0], reverse=True)

            for i, component in enumerate(page_elements):
                pos, element = component[0], component[1]

                if isinstance(element, LTTextContainer):
                    if not table_extraction_flag:
                        line_text, format_per_line = text_extractor.text_extraction(element)
                        page_text.append(line_text)
                        line_format.append(format_per_line)
                        page_content.append(line_text)

                if isinstance(element, LTFigure):
                    image_extractor.crop_image(element, page_obj)
                    image_extractor.convert_to_images('cropped_image.pdf')
                    image_text = image_extractor.image_to_text('PDF_image.png')
                    text_from_images.append(image_text)
                    page_content.append(image_text)
                    page_text.append('image')
                    line_format.append('image')

                if isinstance(element, LTRect):
                    if first_element and (table_num + 1) <= len(tables):
                        lower_side = page.bbox[3] - tables[table_num].bbox[3]
                        upper_side = element.y1
                        table = table_extractor.extract_table(pdf_path, pagenum, table_num)
                        table_string = table_extractor.table_converter(table)
                        text_from_tables.append(table_string)
                        page_content.append(table_string)
                        table_extraction_flag = True
                        first_element = False
                        page_text.append('table')
                        line_format.append('table')
                    elif element.y0 >= lower_side and element.y1 <= upper_side:
                        pass
                    elif not isinstance(page_elements[i + 1][1], LTRect):
                        table_extraction_flag = False
                        first_element = True
                        table_num += 1

        text_per_page['Page_' + str(pagenum)] = [page_text, line_format, text_from_images, text_from_tables,
                                                 page_content]

    # Clean up created files
    os.remove('cropped_image.pdf')
    os.remove('PDF_image.png')

    return text_per_page

if __name__ == "__main__":
    # Example usage
    pdf_path = str(here("./Example PDF.pdf"))
    result = process_pdf(pdf_path)
    print(''.join(result['Page_0'][4]))
