import scrapy


# class QuotesSpider(scrapy.spiders.CrawlSpider):
from scrapy import Request


class QuotesSpider(scrapy.Spider):
    name = 'quotes_spider'
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['http://quotes.toscrape.com/']

    def parse(self, response):
        # yield from self.parse_page(response)
        for url in response.css('.tag-item ::attr(href)').extract()[:1]:
            yield response.follow(url, self.parse_page)

    def parse_page(self, response):
        for quote_s in response.css('.quote'):
            item = {
                'text': quote_s.css('.text::text').get(),
                'author': quote_s.css('.author::text').get(),
                'tags': quote_s.css('.tag::text').extract()
            }
            yield item

        next_url = response.css('.next ::attr(href)').get()
        yield response.follow(next_url, callback=self.parse_page)
