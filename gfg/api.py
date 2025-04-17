from fastapi import FastAPI, HTTPException
from typing import List
from typing import Optional
from pydantic import BaseModel
import pandas as pd
import os

app = FastAPI()

#Load crawled data from the Excel file
file_path = os.path.join(os.path.dirname(__file__), "Wiki_Articles_Parsed.xlsx")
try:
    crawled_data = pd.read_excel(file_path)
    
    #Rename columns to match the Pydantic model with the excel file
    crawled_data = crawled_data.rename(columns={
        "title": "Title",  
        "sections": "Sections", 
        "paragraph": "Paragraph",  
        "references": "References",
        "summary": "Summary" 
    }).fillna("").to_dict(orient="records")  #Replace None with empty strings   
except FileNotFoundError:
    crawled_data = []
except Exception as e:
    crawled_data = []

#Pydantic model for response structure
class CrawledItem(BaseModel):
    Title: Optional[str] = None
    Sections: Optional[str] = None
    Paragraph: Optional[str] = None
    References: Optional[str] = None
    Summary: Optional[str] = None

#Get all crawled data
@app.get("/data", response_model=List[CrawledItem])
def get_all_data():
    """
    Returns all crawled data.
    """
    return crawled_data

#Get data by title
@app.get("/data/{title}", response_model=CrawledItem)
def get_data_by_title(title: str):
    """
    Returns crawled data for a specific title.
    """
    for item in crawled_data:
        if item["Title"].lower() == title.lower():  #Use "Title"
            return item
    raise HTTPException(status_code=404, detail="Item not found")

#Search data by keyword
@app.get("/search", response_model=List[CrawledItem])
def search_data(keyword: str):
    """
    Searches crawled data for a keyword in the title or content.
    """
    results = [
        item for item in crawled_data
        if keyword.lower() in item["Title"].lower() or keyword.lower() in item["Paragraph"].lower()
    ]
    if not results:
        raise HTTPException(status_code=404, detail="No matching items found")
    return results

#Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)