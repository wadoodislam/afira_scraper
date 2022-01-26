import json
import re
from scrapy import Request, Selector
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class BusterAndPunchSpider(CrawlSpider):
    name = 'busterandpunch_spider'
    allowed_domains = ['www.busterandpunch.com']
    start_urls = ['https://www.busterandpunch.com/shop/']

    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    rules = (
        Rule(LinkExtractor(restrict_css='.products'), callback='parse_item'),
        Rule(LinkExtractor(restrict_css='.page-numbers')),
    )

    def parse_item(self, response):
        product_id = response.css('[property="product:retailer_item_id"]::attr(content)').get()
        item = {
            'sku': product_id,
            'title': response.css('.product_title::text').get(),
            'price': int(response.css('.summary bdi::text').get().replace(',', '')),
            'description': '\n'.join(response.css('.product-description__inner p::text').extract()),
            'images': ';'.join(response.css('#gallery a::attr(href)').extract()),
            'line-drawing': response.css('.product-description__spec-image ::attr(src)').get(),
            'included-in-the-box': ';'.join(response.css('#tab-included-in-the-box ::attr(src)').extract()),
            'scale': ';'.join(response.css('#tab-product-scale ::attr(src)').extract()),
            'finish': response.css('.iconic-was-swatches__item ::attr(data-finish)').get(),
            'finish-img-url': response.css('.iconic-was-swatches__item  img::attr(src)').get(),
            'bulb-id': '',
            'bulb-description': '',
            'skus': [],
            'next_requests': self.next_requests(response),
        }
        for spec_mannual_s in response.css('#tab-downloads [data-link-label]'):
            key = spec_mannual_s.css('::attr(data-link-label)').get().replace(' ', '-').lower()
            item[f'{key}'] = spec_mannual_s.css('::attr(href)').get()

        self.get_side_panels(product_id, item, response)
        self.get_variations(product_id, item, response)

        finish_css = 'h2:contains("FINISH") + ul.iconic-was-swatches [data-finish]::attr(href)'
        yield from [Request(url=url, callback=self.parse_item)
                    for url in response.css(finish_css).extract()]

        yield from self.item_or_next_requests(item)

    def next_requests(self, response):
        requests = []

        install_css = '[aria-labelledby="tab-title-installation-video"] script::attr(src)'
        installation = response.css(install_css).get()

        if installation:
            requests.append(Request(response.urljoin(installation), callback=self.parse_installation, dont_filter=True))

        product_video_css = '.product__main-video__wrapper script::attr(src)'
        product_video = response.css(product_video_css).get()

        if product_video:
            requests.append(Request(response.urljoin(product_video), callback=self.parse_product_video, dont_filter=True))

        finish_url_css = '.which-finish__media-wrapper ::attr(src)'
        finish = response.css('[data-active-finish]::text').get()

        for finish_item in response.css('.which-finish__grid-item'):
            if finish_item.css('h3::text').get() == finish:
                requests.append(Request(url=response.urljoin(finish_item.css(finish_url_css).get()), callback=self.parse_finish, dont_filter=True)                    )

        return requests

    def parse_installation(self, response):
        item = response.meta['item']
        item['installation-video'] = json.loads(re.search('\"assets\"\:(\[.*?\])', response.text).group(1))[0]['url']
        yield from self.item_or_next_requests(item)

    def parse_product_video(self, response):
        item = response.meta['item']
        item['product-video'] = json.loads(re.search('\"assets\"\:(\[.*?\])', response.text).group(1))[0]['url']
        yield from self.item_or_next_requests(item)

    def parse_finish(self, response):
        item = response.meta['item']
        try:
            item['finish-media'] = json.loads(re.search(r'"assets":(\[.*?\])', response.text).group(1))[0]['url']
        except:
            item['finish-media'] = response.url
        yield from self.item_or_next_requests(item)

    def item_or_next_requests(self, item):
        requests = item.pop('next_requests')

        if not requests:
            items = []
            skus = item.pop('skus')
            if not skus:
                items.append(item)

            for sku in skus:
                raw_sku = item.copy()
                raw_sku.update(sku)
                items.append(raw_sku)

            return items

        request = requests.pop()
        item['next_requests'] = requests
        request.meta['item'] = item
        return [request]

    def get_side_panels(self, pid, item, response):
        side_panel = response.css('script:contains("const side_panel")::text')
        if side_panel:
            side_panel_s = Selector(text=side_panel.re_first("const\sside_panel\s=\s\$\('(.*?)'\);"))
            for sku_s in side_panel_s.css('.product_box'):
                sku = dict()
                sku['sku'] = f'{pid}-{sku_s.css("::attr(data-value)").get()}'
                sku['bulb-id'] = sku_s.css("::attr(data-value)").get()
                sku['bulb-description'] = sku_s.css("::attr(data-title)").get()
                sku['price'] = item['price'] + int(sku_s.css('::attr(data-price-per-unit)').get())
                sku['images'] = item['images'] + f';{sku_s.css(" img::attr(src)").get()}'
                item['skus'].append(sku)

    def get_variations(self, pid, item, response):
        offers_css = 'script[type="application/ld+json"]:contains(Product)::text'
        offers = json.loads(response.css(offers_css).get())['@graph'][0]['offers'][0].get('offers', [])

        for sku_s in response.css('.variation-radios label, #pa_dimmability + ul li'):
            sku = dict()
            val = sku_s.css("::attr(value), ::attr(data-value)").get()
            sku['sku'] = f'{pid}-{val}'
            sku['price'] = ([offer['price'] for offer in offers if val in offer['name']] or [item['price']])[0]
            item['skus'].append(sku)