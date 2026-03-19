import json
from math import ceil
import urllib.parse

import scrapy

from wb_parser import settings as wb_settings
from wb_parser.items import ProductItem


class WildberriesSpider(scrapy.Spider):
    name = "wildberries"
    allowed_domains = ["wildberries.ru", "wbbasket.ru", "cdn.wbbasket.ru"]
    items_per_page = 100

    def __init__(self, name=None, max_pages="5", **kwargs):
        super().__init__(name=name, **kwargs)
        self.max_pages = int(max_pages)
        self.search_query = wb_settings.SEARCH_QUERY
        self.dest = wb_settings.DEST
        self.search_url_template = wb_settings.SEARCH_URL_TEMPLATE
        self.card_url_template = wb_settings.CARD_URL_TEMPLATE
        self.image_url_template = wb_settings.IMAGE_URL_TEMPLATE
        self.wb_token = wb_settings.X_WBAAS_TOKEN
        self.baskets = []

    def start_requests(self):
        """Start with basket hosts, then go to search."""
        self.logger.info("Starting spider")
        yield scrapy.Request(
            url=wb_settings.BASKETS_URL,
            callback=self.parse_baskets,
            errback=self.handle_error,
        )

    def handle_error(self, failure):
        self.logger.error(f"Request error: {failure.value}")

    def parse_baskets(self, response):
        """Забираем basket-хосты с CDN WB."""
        if response.status != 200:
            self.logger.error(
                f"Baskets request failed with status {response.status}: {response.text[:300]}"
            )
            return

        try:
            data = response.json()
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse baskets JSON: {response.url}")
            return

        self.baskets = data["origin"]["mediabasket_route_map"][0]["hosts"]
        self.logger.info(f"Loaded {len(self.baskets)} basket hosts from CDN")

        if not self.wb_token:
            self.logger.warning("X_WBAAS_TOKEN is empty, search request may fail")

        yield scrapy.Request(
            url=self.search_url_template.format(
                dest=self.dest,
                query=urllib.parse.quote(self.search_query),
                page=1,
            ),
            callback=self.parse_first_page,
            errback=self.handle_error,
            cookies={"x_wbaas_token": self.wb_token},
            meta={"page": 1, "handle_httpstatus_all": True},
            headers={
                "Referer": (
                    "https://www.wildberries.ru/catalog/0/search.aspx"
                    f"?search={urllib.parse.quote(self.search_query)}"
                )
            },
        )

    def parse_first_page(self, response):
        """Read the first search page and count pages."""
        if response.status != 200:
            self.logger.error(
                f"Search page {response.meta['page']} failed with status {response.status}: "
                f"{response.text[:300]}"
            )
            return

        try:
            data = response.json()
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse search JSON: {response.url}")
            return

        total_products = data.get("total", 0)
        total_pages = ceil(total_products / self.items_per_page) if total_products else 1
        total_pages = min(total_pages, self.max_pages)

        self.logger.info(f"Found {total_products} products on {total_pages} pages")

        yield from self.parse_search(response)

        for page in range(2, total_pages + 1):
            yield scrapy.Request(
                url=self.search_url_template.format(
                    dest=self.dest,
                    query=urllib.parse.quote(self.search_query),
                    page=page,
                ),
                callback=self.parse_search,
                errback=self.handle_error,
                cookies={"x_wbaas_token": self.wb_token},
                meta={"page": page, "handle_httpstatus_all": True},
                headers={
                    "Referer": (
                        "https://www.wildberries.ru/catalog/0/search.aspx"
                        f"?search={urllib.parse.quote(self.search_query)}"
                    )
                },
            )

    def parse_search(self, response):
        """Read items from search results."""
        if response.status != 200:
            self.logger.error(
                f"Search page {response.meta['page']} failed with status {response.status}: "
                f"{response.text[:300]}"
            )
            return

        try:
            data = response.json()
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse search JSON: {response.url}")
            return

        products = data.get("data", {}).get("products", [])

        if not products:
            products = data.get("products", [])

        if not products:
            self.logger.error(
                f"No products on page {response.meta['page']}: {response.text[:500]}"
            )
            return

        self.logger.info(f"Page {response.meta['page']}: found {len(products)} products")

        for product in products:
            nm_id = product.get("id")
            if not nm_id:
                continue

            sizes = product.get("sizes", [])
            prices = []
            if sizes:
                for size in sizes:
                    price_info = size.get("price", {})
                    price_raw = price_info.get("product") or price_info.get("basic", 0)
                    if price_raw:
                        prices.append(price_raw / 100)

            price = min(prices) if prices else 0

            product_data = {
                "article": nm_id,
                "name": product.get("name", ""),
                "price": price,
                "rating": product.get("reviewRating", 0),
                "reviews_count": product.get("feedbacks", 0),
                "seller_name": product.get("supplier", ""),
                "seller_id": product.get("supplierId", 0),
                "sizes": sizes,
                "pics_count": product.get("pics", 0),
                "total_stock": product.get("totalQuantity", 0),
            }

            request = self.make_card_request(product_data)
            if request:
                yield request

    def parse_card(self, response):
        """Read one product card."""
        product_data = response.meta["product_data"]
        nm_id = product_data["article"]
        basket = response.meta["basket"]
        self.logger.info(f"Parsing card {response.url}")

        description = ""
        characteristics = {"groups": [], "options": []}

        if response.status != 200:
            self.logger.warning(
                f"Card request failed for {nm_id} with status {response.status}"
            )
            data = {}
        else:
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse card JSON for {nm_id}")
                data = {}

        description = data.get("description", "")

        for group in data.get("grouped_options", []):
            group_name = group.get("group_name", "")
            group_options = []
            for option in group.get("options", []):
                key = option.get("name", "")
                value = option.get("value", "")
                if key:
                    group_options.append({"name": key, "value": value})
            if group_options:
                characteristics["groups"].append(
                    {"group": group_name or "Без группы", "options": group_options}
                )

        if not characteristics["groups"]:
            for option in data.get("options", []):
                key = option.get("name", "")
                value = option.get("value", "")
                if key:
                    characteristics["options"].append({"name": key, "value": value})

        image_urls = self.build_image_urls(nm_id, product_data["pics_count"], basket)

        sizes_list = []
        total_stock = 0
        for size in product_data["sizes"]:
            size_name = size.get("origName") or size.get("name", "")
            if size_name:
                sizes_list.append(size_name)
            for stock_entry in size.get("stocks", []):
                total_stock += stock_entry.get("qty", 0)

        if total_stock == 0:
            total_stock = product_data.get("total_stock", 0)

        seller_id = product_data.get("seller_id", 0)
        seller_url = (
            f"https://www.wildberries.ru/seller/{seller_id}"
            if seller_id
            else ""
        )

        item = ProductItem(
            url=f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx",
            article=nm_id,
            name=product_data["name"],
            price=product_data["price"],
            description=description,
            images=", ".join(image_urls),
            characteristics=characteristics,
            seller_name=product_data["seller_name"],
            seller_url=seller_url,
            sizes=", ".join(sizes_list) if sizes_list else "",
            stock=total_stock,
            rating=product_data["rating"],
            reviews_count=product_data["reviews_count"],
        )

        yield item

    def build_image_urls(self, nm_id: int, pics_count: int, basket: str) -> list:
        """Build image URLs for one product."""
        if pics_count <= 0:
            return []

        vol = nm_id // 100000
        part = nm_id // 1000

        urls = []
        for index in range(1, pics_count + 1):
            urls.append(
                self.image_url_template.format(
                    basket=basket,
                    vol=vol,
                    part=part,
                    nm=nm_id,
                    index=index,
                )
            )

        return urls

    def make_card_request(self, product_data: dict):
        """Build request for card.json."""
        nm_id = product_data["article"]
        vol = nm_id // 100000
        part = nm_id // 1000

        basket = next(
            (
                "https://" + basket_data["host"]
                for basket_data in self.baskets
                if basket_data["vol_range_from"] <= vol <= basket_data["vol_range_to"]
            ),
            "",
        )

        if not basket:
            self.logger.warning(f"Basket not found for article {nm_id}")
            return None

        card_url = self.card_url_template.format(
            basket=basket, vol=vol, part=part, nm=nm_id
        )
        self.logger.info(f"Card request prepared for article {nm_id}")

        return scrapy.Request(
            url=card_url,
            callback=self.parse_card,
            errback=self.handle_error,
            meta={
                "product_data": product_data,
                "basket": basket,
                "handle_httpstatus_all": True,
            },
            headers={"Referer": "https://www.wildberries.ru/"},
        )
