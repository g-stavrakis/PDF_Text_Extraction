from pdfminer.layout import LTChar, LTTextContainer

class PdfTextExtractor:
    def text_extraction(self, element: LTTextContainer):
        """
        Extracts text and its formatting from a text container element.

        Args:
            element (LTTextContainer): A text container element from a PDF document.

        Returns:
            tuple: A tuple containing the extracted text and a list of unique formats per line.
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
