import pdfplumber
from typing import List

class PdfTableExtractor:
    def extract_table(self, pdf_path: str, page_num: int, table_num: int) -> List[List[str]]:
        """
        Extracts a specific table from a specific page of a PDF file.

        Args:
            pdf_path (str): The path to the PDF file.
            page_num (int): The page number to extract the table from.
            table_num (int): The index of the table on the page.

        Returns:
            List[List[str]]: The extracted table as a list of lists, where each sublist represents a row.
        """
        with pdfplumber.open(pdf_path) as pdf:
            table_page = pdf.pages[page_num]
            table = table_page.extract_tables()[table_num]
        return table

    def table_converter(self, table: List[List[str]]) -> str:
        """
        Converts a table into a formatted string representation.

        Args:
            table (List[List[str]]): The table to be converted, represented as a list of rows.

        Returns:
            str: A string representation of the table.
        """
        table_string = ''
        for row in table:
            cleaned_row = [item.replace('\n', ' ') if item is not None and '\n' in item else 'None' if item is None else item for item in row]
            table_string += '|' + '|'.join(cleaned_row) + '|' + '\n'

        table_string = table_string[:-1]  # Removing the last line break
        return table_string
