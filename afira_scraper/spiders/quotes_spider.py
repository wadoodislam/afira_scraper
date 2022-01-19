from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class QuotesSpider(CrawlSpider):
    name = 'quotes_spider1'
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['http://quotes.toscrape.com/']

    rules = (
        Rule(LinkExtractor(restrict_css='.tag-item'), callback='parse_item'),
        Rule(LinkExtractor(restrict_css='.next'), callback='parse_item')
    )

    def parse_item(self, response):
        for quote_s in response.css('.quote'):
            item = {
                'text': quote_s.css('.text::text').get(),
                'author': quote_s.css('.author::text').get(),
                'tags': quote_s.css('.tag::text').extract(),
            }
            yield item
