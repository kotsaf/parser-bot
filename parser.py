import sqlite3
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from lxml import html

def clean_price(price_text):

    # удаляем символы кроме цифр, точки и запятой
    cleaned = re.sub(r'[^\d.,]', '', price_text)
    # меняем запятую на точку для float
    cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None

def parse_prices():
    """Парсинг цен со всех сайтов из базы данных"""
    conn = sqlite3.connect('sources.db')
    df = pd.read_sql_query("SELECT * FROM sources", conn)
    conn.close()

    results = []
    
    for _, row in df.iterrows():
        try:
            # получаем HTML страницы
            response = requests.get(row['url'])
            response.raise_for_status()
            
            # Парсим 
            tree = html.fromstring(response.content)
            elements = tree.xpath(row['xpath'])
            
            if not elements:
                print(f"Не найдены элементы по xpath на сайте {row['title']}")
                continue
                
            prices = []
            for element in elements:
                price_text = element.text_content().strip()
                price = clean_price(price_text)
                if price is not None:
                    prices.append(price)
            
            if prices:
                avg_price = sum(prices) / len(prices)
                results.append({
                    'title': row['title'],
                    'url': row['url'],
                    'average_price': avg_price,
                    'prices_found': len(prices)
                })
            else:
                print(f"Не удалось извлечь цены с сайта {row['title']}")
                
        except Exception as e:
            print(f"Ошибка при парсинге {row['title']}: {str(e)}")
    
    return results

def main():
    results = parse_prices()
    
    if results:
        print("\nРезультаты парсинга:")
        for result in results:
            print(f"\nСайт: {result['title']}")
            print(f"URL: {result['url']}")
            print(f"Средняя цена: {result['average_price']:.2f}")
            print(f"Найдено цен: {result['prices_found']}")
    else:
        print("Не удалось получить цены ни с одного сайта")

if __name__ == '__main__':
    main() 