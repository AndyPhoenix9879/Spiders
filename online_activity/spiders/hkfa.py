import scrapy
import re
from datetime import datetime
from selenium import webdriver
import logging
from selenium.webdriver.remote.remote_connection import LOGGER   

data = {
    'event_name_chi': '',
    'event_name_eng': '',
    'start_date': '',
    'end_date': '',
    'fetch_date': '',
    'description_chi': '',
    'description_eng': '',
    'event_type_chi': '',
    'event_type_eng': '',
    'location_chi': '',
    'location_eng': '',
    'fee': '',
    'organiser_chi': '',
    'organiser_eng': '',
    'source': '',
    'link_chi': '',
    'link_eng': '',
}

count = 0

class HkfaSpider(scrapy.Spider):
    name = 'hkfa'
    # allowed_domains = ['www.filmarchive.gov.hk/en_US/web/hkfa/programmesandexhibitions/evecal.html']
    # custom_settings = {
    #     'CONCURRENT_REQUEST': 1,
    # }
    start_urls = ['http://www.filmarchive.gov.hk/en_US/web/hkfa/programmesandexhibitions/evecal.html']

    def cleanText(self, string):
        string = re.sub("</?[^>]*>", "", str(string))
        string = string.strip("[]").strip("'")
        string = string.replace("\\n", "")
        string = string.replace("\\t", "")
        string = string.replace("\\r", " ")
        string = string.replace("\n", "")
        string = string.replace("\t", "")
        string = string.replace("\r", " ")
        string = string.replace("\\xa0", "")
        string = string.replace("\xa0", "")
        string = string.replace("#", "")
        return string

    def parse(self, response):
        # LOGGER.setLevel(logging.WARNING)
        PATH = "/Users/andylai/chromedriver"
        driver = webdriver.Chrome(PATH)
        driver.get(response.url)

        # # Easier to handle these data directly using Selenium syntaxes - there was a consistent xpath 
        urls = driver.find_elements_by_xpath("//*[@id='article']/table[@class='table_main']//a")
        name = driver.find_elements_by_xpath("//*[@id='article']/table[@class='table_main']/tbody//td[position() mod 3 = 0]")
        # date = driver.find_elements_by_xpath("//*[@id='article']/table[@class='table_main']/tbody//td[position() = 1 or position() mod 6 = 0]")
        price = driver.find_elements_by_xpath("//*[@id='article']/table[@class='table_main']/tbody//td[position() mod 4 = 0]")
        
        # data["fetch_date"] = datetime.now()

        for i in range(len(name)):
            test.append(name[i].text.replace("\n", ", "))
        # # data["event_name_eng"] = name

        # # Cleanup of the scrape data for dates happens within this for loop
        # for things in date:
        #     # Regular expression to remove contents inside parenthesis ( ... )
        #     date_cleaned = re.sub("\([^)]*\)", "", str(things.text))
        #     dates = date_cleaned.split(" - ")
        #     for i in range(len(dates)):
        #         dates[i] = dates[i].strip()
            
        #     if (len(dates) > 0):
        #         data["start_date"] = datetime.strptime(dates[0], "%d %B %Y")
        #         if len(dates) == 2:
        #             data["end_date"] = datetime.strptime(dates[1], "%d %B %Y")
        #         else:
        #             data["end_date"] = ""
            
        for things in price:
            data["fee"] = things.text.split("\n")[0]

        links = []
        for url in urls:
            links.append(url.get_attribute("href"))
        
        for i in range(len(links)-1):
            for j in range(i+1, len(links)):
                if (links[i] == links[j]):
                    links[j] = ""
                    # urls[j] = ""
        
        for link in links:
            if (link != ""):
                yield scrapy.Request(link, callback=self.parse_events)

    def parse_events(self, response):
        
        # name handler
        name = response.xpath('//*[@id="title_bar_left"]/text()').extract_first()
        # //*[@id="article"]/div[2]/div/table/tbody/tr/th/p/span/strong
        if (name == "Film Screenings"):
            name = response.xpath('//*[@id="article"]//p/span/strong/text()').extract_first()
        
        if (name == None):
            name = response.xpath('//div[@class="application"]/h1/text()').extract()
            # cleaning up
            tmp = name
            name = ""
            for text in tmp:
                name += text
            name = self.cleanText(name)
        
        data["event_name_eng"] = name
        # End of handle of name
        
        # Handle description
        description = response.xpath("//*[@id='article']/div/div/div/div/p[position() >= 3]/text()").extract()

        if (len(description) == 0):
            description = response.xpath("//*[@id='article']/p[position() >= 2]/text()").extract()
            if (len(description) == 0):
                description = response.xpath("//article/div/div[3]/div[@class='span12 doppelTeaser']/text()[8]").extract()
        
        desc = ""
        for i in range(len(description)):
            desc += self.cleanText(description[i])

        data["description_eng"] = desc.strip() 
        # End of handle of description

        # Handle location
        location = response.xpath("//*[@id='article']/div/div/div/div/p[2]/strong/text()").extract()

        if (len(location) == 0):
            location = response.xpath("//*[@id='article']/table[@class='table_main']/tbody/tr[2]/td[3]/text()").extract_first()
            if (location == None):
                location = response.xpath("//div[@class='teaserBox']/h2/text()").extract_first().strip()
            else:
                location = location.strip()
        else:
            location = location[1].replace("Venue：", "").strip()
            
        data["location_eng"] = location
        # End of handle of location 

        # Handle date
        dates = response.xpath('//*[@id="article"]/div/div/div/div/p[2]/strong/text()[1]').extract()
        
        if (len(dates) == 0):
            dates = response.xpath('//*[@id="article"]/table[@class="table_main"]/tbody/tr[position() >= 2]/td[1]/text()').extract()
            if (len(dates) == 0):
                dates = response.xpath('/html/body/div[1]/div[3]/div[1]/div/article/div/div[1]/div/p[1]/text()').extract()
        
        for i in range(len(dates)):
            dates[i] = self.cleanText(dates[i])
            dates[i] = re.sub("\([^)]*\)", "", dates[i])
            dates[i] = dates[i].replace("Date：", "")
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for d in days:
                replace_this = d + ", "
                dates[i] = dates[i].replace(replace_this, "")
            dates[i] = dates[i].strip()

        if " - " in dates[0]:
            dates = dates[0].split(" - ")
            start_date = datetime.strptime(dates[0], "%d/%m/%Y")
            end_date = datetime.strptime(dates[1], "%d/%m/%Y")
        else:
            if "." in dates[0]:
                start_date = datetime.strptime(dates[0], "%d.%m.%Y")
                end_date = ""
            else:
                start_date = []
                try:
                    for i in range(len(dates)):
                        start_date = datetime.strptime(dates[i], "%d/%m/%Y")
                except:
                    for i in range(len(dates)):
                        dates[i] += "/" + str(datetime.today().year)
                        
                        start_date.append(datetime.strptime(dates[i], "%d/%m/%Y"))
                end_date = ""

        data["start_date"] = start_date
        data["end_date"] = end_date
        data["fetch_date"] = datetime.now()
        # End of handle of date

        data["source"] = "Hong Kong Film Archive"
        data["link_eng"] = response.url

        # Handle fee
        fee = response.xpath('//*[@id="article"]/div/div/div/div/p[2]/text()').extract()
        if (len(fee) == 0):
            fee_link = response.url.replace("https://", "").split("/")
            fee_link[len(fee_link)-1] = "ticketinfo.html"
            ticket_link = ""
            for link in fee_link:
                ticket_link += link + "/"
            ticket_link = ticket_link.rstrip("/")
            # r = scrapy.Request("https://"+ticket_link, callback=self.get_fee, meta=data)
            # yield r
        else:
            data["fee"] = fee
        # //aside/p[1]/text()[2]
        # End of handle of fee

        

        
        yield data    
        #     yield scrapy.Request(response.url.replace('/en_US/', '/zh_TW/'), callback=self.parse_cn, meta=data)

    def get_fee(self, response):
        data = response.meta
        fee = response.xpath('//*[@id="article"]/p[span/strong/text()[contains(., "Tickets:" ) or contains(., "Tickets:")]]//text()').extract()
        print("\n\n\n")
        print("This link ", response.url)
        print(fee)
        print("\n\n\n")
        data["fee"] = fee
        yield data
    # def parse_cn(self, response):