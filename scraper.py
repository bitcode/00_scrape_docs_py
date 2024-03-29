import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse, urljoin, urldefrag
import logging
from collections import deque
import time


def is_valid_link(url, base_domain, start_path):
    """Check if a URL is valid, within the specified domain and path, and not a media file."""
    parsed_url = urlparse(url)
    if parsed_url.scheme in ["http", "https"] and \
       parsed_url.netloc == base_domain and \
       parsed_url.path.startswith(start_path) and \
       not parsed_url.path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf')):
        return True
    return False


def extract_links(url, content, base_domain, start_path):
    """Extract all valid links from the HTML content, normalize, and filter them."""
    soup = BeautifulSoup(content, 'html.parser')
    links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(url, href)  # Ensure the URL is absolute
        full_url, _ = urldefrag(full_url)  # Remove URL fragment
        if is_valid_link(full_url, base_domain, start_path):
            links.add(full_url)
    return links


def scrape_page(start_url, base_domain, start_path, delay=1):
    visited = set()
    queue = deque([start_url])

    while queue:
        url = queue.popleft()
        if url not in visited:
            try:
                # Introduce a delay to avoid overloading the server
                time.sleep(delay)
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    visited.add(url)
                    logging.info(f'Successfully downloaded {url}')
                    save_content(response.text, url, base_domain, start_path)
                    links = extract_links(
                        url, response.text, base_domain, start_path)
                    for link in links:
                        if link not in visited:
                            queue.append(link)
                else:
                    logging.error(f'Failed to retrieve {
                                  url} - Status code: {response.status_code}')
            except Exception as e:
                logging.error(f'Error during requests to {url} : {str(e)}')


def save_content(content, url, base_domain, start_path):
    parsed_url = urlparse(url)
    local_file_path = parsed_url.path.lstrip('/')
    directory = os.path.join(
        'downloaded_html', base_domain, os.path.dirname(local_file_path))
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, os.path.basename(
        local_file_path) or 'index.html')

    if not os.path.exists(filepath):  # Check if the file already exists
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        logging.info(f'Saved content to {filepath}')
    else:
        logging.info(f'Content already downloaded: {filepath}')
