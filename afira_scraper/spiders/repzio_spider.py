import scrapy
from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import json

class RepzioSpider(CrawlSpider):
    name = 'repzio_spider'
    allowed_domains = ['repzio.com']
    start_urls = ['https://app.repzio.com']
    custom_settings = {
        'COOKIES_ENABLED': True
    }

    rules = (
         Rule(LinkExtractor(restrict_css='.main-category')),
         Rule(LinkExtractor(restrict_css='.product'), callback='parse_item')
    )

    handle_httpstatus_list = [400]

    def start_requests(self):
        return [Request(url=self.start_urls[0], callback=self.parse_login_page)]

    def parse_login_page(self, response):
        payload = {
            'ReturnUrl': response.css('#ReturnUrl::attr(value)').get(),
            'Username':'jon.mcmahan@ktrlighting.com',
            'Password':'@Winner8248',
            'button':'login',
            '__RequestVerificationToken':response.css('[name=__RequestVerificationToken]::attr(value)').get(),
            'RememberLogin':'false',
        }
        return scrapy.FormRequest(url=response.url, formdata=payload, callback=self.parse_token, dont_filter=True)

    def parse_token(self, response):
        payload = {
            'code': response.css('[name=code]::attr(value)').get(),
            'id_token': response.css('[name=id_token]::attr(value)').get(),
            'scope': response.css('[name=scope]::attr(value)').get(),
            'state': response.css('[name=state]::attr(value)').get(),
            'session_state': response.css('[name=session_state]::attr(value)').get() ,
        }
        return scrapy.FormRequest(url=response.css('form::attr(action)').get(), formdata=payload, callback=self.parse_menu, dont_filter=True)

    def parse_menu(self, response):
        return Request('https://app.repzio.com/manufacturers/1616/dashboard', callback=self.parse_client)
        #return Request('https://app.repzio.com/manufacturers/1616/clients/2000679/categories/1056839/products/fm-63216-bk/', callback=self.parse_item)

    def parse_client(self, response):
        url = response.css('.table td:nth-child(3) a::attr(href)').get()
        yield response.follow(url+'/categories')

    def parse(self, response, **kwargs):
        if response.status == 400:
            i = 0
        yield from super().parse(response)

    def parse_item(self, response):
        if response.status == 400:
            i = 0
        raw_item = json.loads(response.css('script:contains(productApp)::text').re_first('product: ({.*}),'))
        item = {

                'picture': response.css('.img-wrap ::attr(src)').get(),
                'price': response.css('.price-wrap h5::text').get().strip(),
                'title': response.css('.col-md-7 h3 ::text').get(),
                'sku': response.css('.col-md-7 h4 ::text').get().strip(),
        }
        for li in response.css('.description-wrap::text').getall():
            if li.strip():
                key, value = li.strip().split(':')
                item[f'{key}'] = value
        yield item
