from Pipeline.user_resume import Resume
from Pipeline.description_topandas import StructureData
from Pipeline.job_description import Scraper


class PipeLine:
    def __init__(self):
        super().__init__()
    
    def run(self):
        # Extracting the Resume Info 
        path = input('Enter Resume Path : ')
        resume = Resume(path)
        resume_info = resume.extract_info()

        # Extracting the job info from website 
        web_path = input('Enter The Website Path : ')
        crawler = Scraper(web_path)
        job_info = crawler.run()

        out_path =  'output/scrape_heading_task.json'
        data_provider = StructureData(out_path)
        df = data_provider.data()

        return resume_info,job_info,df

