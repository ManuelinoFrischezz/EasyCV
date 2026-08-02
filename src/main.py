from extraction import PdfManager


def main():
    # 1. PDF data extraction
    pdf_manager = PdfManager("CVBernardini.pdf")
    pdf_manager.extract_pdf_info()

    # 2. Data schema creation


if __name__ == "__main__":
    main()
