import pdfplumber 


class Resume:
    def __init__(self,pdf_path):
        super().__init__()
        self.path = pdf_path

    
    def extract_info(self):
        text = []
        with pdfplumber.open(self.path) as pdf:
            for page in pdf.pages: #if one page then it runs only one time 
                text.append(page.extract_text() or "")
                print(text)
        return '\n'.join(text)





