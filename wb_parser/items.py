import scrapy


class ProductItem(scrapy.Item):
    # Ссылка на товар
    url = scrapy.Field()
    # Артикул (id на WB)
    article = scrapy.Field()
    # Название товара
    name = scrapy.Field()
    # Цена в рублях
    price = scrapy.Field()
    # Описание
    description = scrapy.Field()
    # Ссылки на фото через запятую
    images = scrapy.Field()
    # Характеристики (структура)
    characteristics = scrapy.Field()
    # Продавец
    seller_name = scrapy.Field()
    # Ссылка на продавца
    seller_url = scrapy.Field()
    # Размеры через запятую
    sizes = scrapy.Field()
    # Остаток по товару
    stock = scrapy.Field()
    # Рейтинг
    rating = scrapy.Field()
    # Количество отзывов
    reviews_count = scrapy.Field()
