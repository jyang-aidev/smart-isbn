import json
import re
import requests

from bs4 import BeautifulSoup
import json

def parse_book_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    author = None
    title = None

    # Method 1: Extraction from the JSON-LD block (Most reliable for Title/Author)
    json_data = soup.find('script', type='application/ld+json')
    if json_data:
        data = json.loads(json_data.string)
        title = data.get('name')
        # Authors can be a list or a single dictionary
        authors = data.get('author', [])
        author = authors[0].get('name') if authors else "Unknown"
    
    if not title:
        # Method 2: Fallback to Meta tags or Title tag if JSON-LD is missing
        title = soup.find('meta', property='og:title')
        title = title['content'] if title else soup.title.string.replace('(豆瓣)', '').strip()
    
    if not author:
        author = soup.find('meta', property='book:author')
        author = author['content'] if author else "Unknown"

    # Find the publisher and publish date
    publisher = ""
    publish_date = ""

    info_div = soup.find('div', id='info')
    info_text = info_div.get_text()

    for line in info_text.split('\n'):
        if "出版年:" in line:
            publish_date = line.replace("出版年:", "").strip()

    # Find the span that contains '出版社:'
    publisher_label = info_div.find('span', string=lambda text: text and '出版社' in text)
    
    if publisher_label:
        # The publisher name is usually the next sibling (either an <a> tag or text)
        publisher_data = publisher_label.next_sibling
        
        # If it's a link (like in Douban), move to the next element
        if publisher_data.name == 'a' or not publisher_data.strip():
            publisher = publisher_label.find_next('a').get_text(strip=True)
        else:
            publisher = publisher_data.strip()            

    return {"title": title, "author": author, "publisher": publisher, "publish_date": publish_date}

def get_traditional_book_details(isbn):  
    """Replaces the Selenium version using Google Books API"""
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "items" in data:
            # Extract info from the first result
            volume_info = data["items"][0]["volumeInfo"]
            
            return {
                "title": volume_info.get("title", "Unknown"),
                "author": ", ".join(volume_info.get("authors", ["Unknown"])),
                "publisher": volume_info.get("publisher", "Unknown"),
                "publish_date": volume_info.get("publishedDate", "Unknown"),
                "isbn": isbn
            }
    except Exception as e:
        print(f"API Error: {e}")
    
    return None

def get_sim_book_details(isbn):
    """Retrieves book info using requests instead of Selenium"""
    
    # Douban requires a User-Agent header, otherwise you will get a 403 Forbidden error
    url = f"https://book.douban.com/isbn/{isbn}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # Use requests to get the page
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if the request was successful
        if response.status_code == 200:
            html_content = response.text
            #with open("html.txt", "w", encoding="utf-8") as f:
            #    f.write(html_content)

            return parse_book_info(html_content)
        else:
            print(f"Error: Received status code {response.status_code}")
            return None
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return None