import scrapy 
import pandas as pd

from gfg.items import ArticleItem
  
class WikiSpider(scrapy.Spider):
    name = "Wiki_spider"
    start_urls = ['https://en.wikipedia.org/wiki/Marine_reptile']

    def __init__(self, *args, **kwargs):
        super(WikiSpider, self).__init__(*args, **kwargs)
        self.articles = []  # List to store scraped data

    def parse(self, response):
        """
        Gets the starting URL and all links on the page. It then follows each link until count reaches 30. 
        Skips count if page is not english and skips the url if it leads to a non-english page.
        """
        if not self.is_english_page(response):
            return
        
        #Extract article URLs and follow them
        for article_url in response.xpath('//a/@href').getall():
            if self.is_english_url(article_url):  #Ensure the URL leads to an English page
                yield response.follow(article_url, self.parse_article)
        pass

    def parse_article(self, response):
        """
        Helper function for parse to store relevant data into ArticleItems for ease of storage
        """
        if not self.is_english_page(response):
            return
        
        #Create an ArticleItem instance
        item = ArticleItem()
        
        #Extract data using XPath
        item['Title'] = response.xpath("//title/text()").get()
        item['Sections'] = [div.xpath('.//h2/text()').get() 
                    for div in response.xpath('//div[contains(@class, "mw-heading mw-heading2")]') 
                    if div.xpath('.//h2/text()').get() not in ['See also', 'References', 'Further reading', 'External links']]
        item['Paragraph']= [self.paragraph(response)]
        item['References']= [li.xpath('.//span[@class="reference-text"]/cite/a/@href').get() 
                    for li in response.xpath('//div[@class="mw-references-wrap mw-references-columns"]//ol[@class="references"]/li')
                    if li.xpath('.//span[@class="reference-text"]/cite/a/@href').get() is not None]

        #Append the item to the list
        self.articles.append(item)

    def closed(self, reason):
        """
        Save the data to an excel file when the spider is finished
        """
        #Convert the list of items to a DataFrame
        df = pd.DataFrame([dict(article) for article in self.articles])

        #Apply the function to all columns in the DataFrame
        df = df.applymap(self.format_string)
        #Save the DataFrame to an Excel file
        df.to_excel('Wiki_Articles.xlsx', index=False)
        
    def is_english_page(self, response):
        """
        Check if the page is in English.
        """
        #Check the URL
        if not response.url.startswith('https://en.wikipedia.org/'):
            return False

        #Check the HTML lang attribute
        language = response.xpath('//html/@lang').get()
        if language and language.startswith('en'):
            return True

        return False
    
    def is_english_url(self, url):
        """
        Check if the URL leads to an English page.
        """
        return url.startswith('/wiki/') or url.startswith('https://en.wikipedia.org/wiki/')
    
    def paragraph(self, response):
        """
        Find and parse the summary paragraph in each page, usually the top paragraph.
        """
        first_div = response.xpath('//div[contains(@class, "mw-heading mw-heading2")]')
        cleaned_text=[]
        if not first_div:
            return

        first_div = first_div[0]
        #Loop through all <p> tags that appear before the <div> in the document
        for p in first_div.xpath('./preceding::p'):
            #Extract the text content of the <p> tag
            cleaned_text.append(p.xpath('.//text()').getall())
        
        cleaned_text=self.flatten(cleaned_text)
        cleaned_text=self.clean(cleaned_text)
        return cleaned_text

    def flatten(self, nested_list):
        """
        Wikipedia contains many embedded characters and links in <p> tag that are appended as nested lists. This flattens the list.
        """
        flat_list = []
        for item in nested_list:
            if isinstance(item, list):  #If the item is a list, recursively flatten it
                flat_list.extend(self.flatten(item))
            else:
                flat_list.append(item)  #Otherwise, add the item to the flat list
        return flat_list

    def clean(self, elements):
        """
        Wikipedia contains many embedded characters and links in <p> tag. This cleans the list of special chars and newlines.
        """
        cleaned_list = []  #Initialize a list to store cleaned strings
        for element in elements:
            if isinstance(element, str):  #Only process strings
             #Remove unwanted characters such as special characters and newlines
                cleaned = ''.join(char for char in element if (char.isalnum() or char.isspace()or char == '.') and char !='\n')
                cleaned_list.append(cleaned)  
        return ' '.join(cleaned_list) 
    
    def format_string(self,value):
        """
        Takes the DataFrame and turns all the lists in each index into a string seperated by a comma
        """
        if isinstance(value, list):
            return ', '.join(map(str, value))
        return value