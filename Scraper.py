import requests
from bs4 import BeautifulSoup
from LogDecorator import LogDecorator
from google_utils import upload_string_to_bucket, download_as_string
import sys
from datetime import datetime
import hashlib


class Scraper():

    def __init__(self, ad_list, **kwargs):
        self.ad_list = ad_list


    @LogDecorator()
    def scrape(self, count):
        # TODO : Add abstraction via generator function to allow counts > one page of ads
        result_page = requests.get(self.ad_list)
        result_soup = BeautifulSoup(result_page.text, 'html.parser')

        # Scrape all ad URLs from ad list page
        urls = []
        for ad_title in result_soup.find_all('a', {'class':'result-title'}):
            urls.append(ad_title['href'])

        # Pull the ledger to check if we've DL'd the ad already
        bucket_ledger = f'craigslist/ledger.txt'
        ledger = download_as_string('craig-the-poet', bucket_ledger)
        hashes = ledger.split('\n')

        time = str(datetime.now())

        successful_uploads = 0
        for i, url in enumerate(urls):
            try:
                ad_obj = self.craigslist_scrape_ad(url)
                title = ad_obj['title']
                body = ad_obj['body']
                city = self.get_city_from_url(url)
                hash = hashlib.sha256(ad_obj['body'].encode()).hexdigest()

                # If we've seen the hash, skip this ad
                if hash in hashes:
                    continue

                # Add hash to seen hashes and upload this ad
                metadata = {
                    'url': url,
                    'hash': hash,
                    'used': False
                }

                text = title + '\n' + body

                upload_string_to_bucket('craig-the-poet', text, f'craigslist/{city}/{time}-{i}.txt', metadata)

                successful_uploads += 1
                hashes.append(hash)

                if successful_uploads == count:
                    break
            except:
                pass

        new_ledger = '\n'.join(hashes)
        upload_string_to_bucket('craig-the-poet', new_ledger, bucket_ledger)



    # TODO: Only works for CL
    @LogDecorator()
    def get_city_from_url(self, url):
        return url.replace('http://', '').replace('https://', '').split('.')[0]



    # TODO: Make more sophisticated. Handle cases where e.g. CL ad is titles YELP BOY TASTY
    @LogDecorator()
    def classify(self, url):
        if 'craigslist' in url:
            return 'craigslist'

        if 'yelp' in url:
            return 'yelp'


    # TODO: Add more scrapers for more sites
    @LogDecorator()
    def craigslist_scrape_ad(self, ad_url):
        result_page = requests.get(ad_url)
        result_soup = BeautifulSoup(result_page.text, 'html.parser')

        # Get Craigslist title
        result_title_element = result_soup.find(id='titletextonly')
        result_title = result_title_element.text

        # Get Craigslist body
        result_body_element = result_soup.find(id='postingbody')
        bad_text = 'QR Code Link to This Post'
        result_text = [x for x in result_body_element.text.split('\n') if x != bad_text and x != '']
        result_body = '\n'.join(result_text)

        return {'title': result_title, 'body': result_body}


if __name__ == '__main__':
    s = Scraper(sys.argv[-1])
    s.scrape(4)
