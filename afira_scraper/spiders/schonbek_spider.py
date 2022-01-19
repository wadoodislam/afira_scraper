from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class SchonbekSpider(CrawlSpider):
    name = 'schonbek_spider'
    allowed_domains = ['schonbek.com']
    start_urls = ['https://www.schonbek.com']
    listing_css = ['ul[data-menu="menu-908"]', '.pages']

    rules =(
        Rule(LinkExtractor(restrict_css=listing_css)),
        Rule(LinkExtractor(restrict_css='.product-item-info'), callback='parse_item')
    )

    def parse_item(self, response):
        item = {
            'Title' : response.css('.base::text').get().strip(),
            'Sku': response.css('.prod-name::text').get(),
            'Download_specs': response.css('.icon-link::attr(href)').extract()[1]
        }
        yield item