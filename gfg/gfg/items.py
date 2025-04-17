# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class ArticleItem(scrapy.Item):
    Title = scrapy.Field() # article title
    Sections = scrapy.Field() #section headers
    Paragraph  = scrapy.Field() #summary paragraph
    References = scrapy.Field() #reference list
