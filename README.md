# Text Extraction from PDFs

<img src="Cover Image.png" width="950" height="500">

In this repo, I will provide a comprehensive guide on extracting text data from PDF files in Python.
This approach will cover the text extraction for different components in PDFs such as:
- Plain text
- Tables
- Images in the PDF

For the full guide you can read my article on Medium: https://bit.ly/3RtPuCw

To achieve that we will use the **PDFMiner** library to perform an initial analysis of the layout of the PDF and identify the proper tool needed for the specific component.
Then based on the component found we will apply the appropriate function and Python Library. 

The output of this process will be a Python dictionary containing information extracted for each page of the PDF file. Each key in this dictionary will present the page number of the document, and its corresponding value will be a list with the following 5 nested lists containing:
1. The text extracted per text block of the corpus
2. The format of the text in each text block in terms of font family and size
3. The text extracted from the images on the page
4. The text extracted from tables in a structured format
5. The complete text content of the page

You can see a flowchart of the process below:

<img src="Text Extraction Flowchart.png" width="500" height="1000">

To extract text from Plain Corpus:
-
- We use the get_text() method of the LTTextContainer element provided be **PDFMiner** to extract the text presented in the container.
- We iterate through the LTTextContainer object to access each LTTextLine object and then we access each individual character element as LTChar collecting the metadata for its fromat

To extract text from Images:
- 
- We use crop_image() function to find the coordinates of the image box detected from **PDFMiner** and then to crop and save it as a new PDF in our directory using the **PyPDF2** library.
- We employ the convert_from_file() function from the **pdf2image** library to convert all PDF files in the directory into a list of images, saving them in PNG format.
- We use the **Image** package of the **PIL** module and implement the image_to_string() function of pytesseract to extract text from the images using the tesseract OCR engine.

To extract text from Tables:
-
-  We employ the extract_table() function, utilising the **pdfplumber** library,to extract the contents of the table into a list of lists
- We table_converter() to join the contents of those lists in a table-like string.
