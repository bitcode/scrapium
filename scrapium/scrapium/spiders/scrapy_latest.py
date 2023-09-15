import scrapy
import datetime
import html
import re

class ScrapyLatestSpider(scrapy.Spider):
    name = "scrapy_latest"
    allowed_domains = ["docs.scrapy.org"]
    start_urls = ["https://docs.scrapy.org/en/latest/"]

    def parse(self, response):
        content_type = response.headers.get('Content-Type', b'').decode()
        if 'text' not in content_type:
            return

        content = response.xpath(
            'string(//div[@role="main"])').get().replace('\n', ' ').replace('¶', '')

        # List of HTML tags to remove
        tags_to_remove = ['span', 'div', 'a', 'p', 'br', 'strong', 'em']

        # Create a regular expression pattern that matches the tags in the list
        pattern = '|'.join(f'<{tag}.*?>|</{tag}>' for tag in tags_to_remove)

        code_blocks = [re.sub(pattern, '', html.unescape(code_block)) for code_block in response.xpath(
            '//div[@role="main"]//pre').getall()]

        link_list = []
        non_header_links = []

        for link in response.xpath('//div[@role="main"]//a'):
            href = link.xpath('@href').get()
            text = link.xpath('string(.)').get()

            if not href.startswith('#') and not href.startswith('mailto:') and text is not None:
                link_list.append({"text": text, "href": href})
                non_header_links.append(link)

        version = response.xpath(
            '//title/text()').re_first(r'Scrapy (\d+\.\d+)')

        yield {
            "url": response.url,
            "content": content,
            "code_blocks": code_blocks,
            "links": link_list,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "version": version
        }

        for link in non_header_links:
            next_url = link.xpath('@href').get()
            yield scrapy.Request(response.urljoin(next_url), callback=self.parse, meta={'parent_url': response.url})
