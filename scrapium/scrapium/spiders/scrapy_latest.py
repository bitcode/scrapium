import scrapy
import datetime
import html
import re
from dateutil.parser import parse


class ScrapyLatestSpider(scrapy.Spider):
    name = "scrapy_latest"
    allowed_domains = ["docs.scrapy.org"]
    start_urls = ["https://docs.scrapy.org/en/latest/"]

    def parse(self, response):
        content_type = response.headers.get('Content-Type', b'').decode()
        if 'text' not in content_type:
            return

        # Search for the revision and last_updated text within the page
        footer_text = response.xpath('string(//footer)').get()

        # Use regular expressions to extract the revision and last updated date
        revision_match = re.search(r'Revision (\w+)', footer_text)
        last_updated_match = re.search(
            r'Last updated on ([\w\s]+)', footer_text)

        revision = revision_match.group(1) if revision_match else None
        last_updated_text = last_updated_match.group(
            1) if last_updated_match else None

        # If found, convert the date string to a standardized format
        if last_updated_text:
            last_updated = parse(last_updated_text).strftime('%Y-%m-%d')
        else:
            last_updated = None

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
            "version": version,
            "revision": revision,
            "last_updated": last_updated,
        }

        for link in non_header_links:
            next_url = link.xpath('@href').get()
            yield scrapy.Request(response.urljoin(next_url), callback=self.parse, meta={'parent_url': response.url})
