import pandas as pd 
import json
import re 

class StructureData:
    def __init__(self, path):
        super().__init__()
        self.path = path

    def clean_text(self):
        
        encodings = ['utf-8','cp1252','latin-1']
        raw = None
        
        for enc in encodings:
            try:
                with open(self.path, 'r', encoding=enc) as f:
                    raw = json.load(f)
                break
            except UnicodeDecodeError:
                continue
        
        if raw is None:
            raise ValueError("Cant able to decode")
        
        cleaned_text = {}
        for key,val in raw.items():
            text = re.sub(r'^[a-zA-Z0-9]', '', val)
            text = re.sub(r'\s+', ' ', text).strip()
            cleaned_text[key] = text

        return cleaned_text

    def data(self):
        raw = self.clean_text()
        df = pd.DataFrame([raw])
        return df

# path = 'output/scrape_heading_task.json'
# data = StructureData(path)
# df = data.data()
# print(df.info())



