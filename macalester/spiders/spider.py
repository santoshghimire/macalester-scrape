# -*- coding: utf-8 -*-
import csv
import scrapy
from scrapy.http.request import Request

from macalester.items import Item


def get_popular_names():
    with open('namelist.csv') as namefile:
        csvreader = csv.reader(namefile)
        return [i[0].lower().strip() for i in list(csvreader)]


class MSpider(scrapy.Spider):
    """
    Scraper to scrape the students details.
    """
    name = "macalester"
    base_url = 'https://webapps.macalester.edu/directory/search/?name='
    allowed_domains = ["https://webapps.macalester.edu/"]

    def __init__(self, lost_pet=None):
        # read names from csv
        self.all_names = get_popular_names()

    def start_requests(self):
        # construct the results url
        name = self.all_names[0]
        url = self.get_default_url(name)
        yield Request(url, self.parse)

    def get_default_url(self, name):
        name = name.replace(" ", "+")
        return self.base_url + name

    def get_next_name(self, name):
        """
        Get next name from the namelist
        """
        try:
            index = self.all_names.index(name)
        except:
            index = -1
        return self.all_names[index + 1]

    def get_name_from_url(self, url):
        qs = url.split("?")[-1]
        name_qs = [i for i in qs.split('&') if i.startswith('name')][0]
        name = name_qs.split('=')[-1]
        return name

    def split_names(self, full_name):
        name_parts = full_name.split(" ")
        first_name = name_parts[0]
        if len(name_parts) == 1:
            middle_name = ""
            last_name = ""
        elif len(name_parts) == 2:
            middle_name = ""
            last_name = name_parts[-1]
        else:
            last_name = name_parts[-1]
            middle_name = " ".join(name_parts[1:-1])
        return first_name, middle_name, last_name

    def parse(self, response):
        """
        Parse the content.
        """
        name = self.get_name_from_url(response.url)

        records = response.xpath(
            "//form[@class='search-box'][@name='SearchForm']/"
            "following-sibling::div[@class='panel']/"
            "div[@class='panel-head']/h2[contains(text(), 'Students')]/"
            "parent::div[@class='panel-head']/following-sibling::p"
        )
        for record in records:
            item = Item()
            full_name = record.xpath("./strong/text()").extract_first()
            item['first_name'], item['middle_name'], item['last_name'] = \
                self.split_names(full_name)
            item['email'] = record.xpath("./a/text()").extract_first()
            yield item
        if not records:
            print("{}: No records found".format(name))
        else:
            print("{}: Records found, crawling".format(name))
        # Scrape for next name
        next_name = self.get_next_name(name)
        next_url = self.get_default_url(next_name)
        yield scrapy.Request(
            next_url, self.parse, dont_filter=True)
