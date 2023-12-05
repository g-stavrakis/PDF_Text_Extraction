from pdfminer.layout import LTChar, LTTextContainer
from typing import Tuple, List

class PdfTextExtractor:
    def text_extraction(self, element: LTTextContainer) -> Tuple[str, List[any]]:
        """
        Extracts text and its formatting from a text container element.

        Args:
            element (LTTextContainer): A text container element from a PDF document.

        Returns:
            Tuple[str, List[any]]: A tuple containing the extracted text (as a string) and
                                    a list of unique formats (font names and sizes) per line.
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
