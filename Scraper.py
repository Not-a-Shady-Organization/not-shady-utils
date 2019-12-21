import requests
from bs4 import BeautifulSoup
from LogDecorator import LogDecorator
from google_utils import upload_string_to_bucket, download_as_string
import sys
from datetime import datetime
import hashlib


class Scraper():

    def __init__(self, **kwargs):
        pass

    def get_ledger(self, ledger_filepath):
        # Either download the ledger, or create one, then download it
        try:
            ledger = download_as_string('craig-the-poet', ledger_filepath)
        except:
            upload_string_to_bucket('craig-the-poet', '', ledger_filepath)
            ledger = download_as_string('craig-the-poet', ledger_filepath)
        return ledger


    LogDecorator()
    def scrape_ad_to_bucket(self, ad_url, bucket_dir=None):
        # Pull the ledger to later check if we've DL'd the ad already
        bucket_ledger = f'craigslist/ledger.txt'
        ledger = self.get_ledger(bucket_ledger)
        hashes = ledger.split('\n')

        time = str(datetime.now())

        # Get the ad
        obj = self.scrape_craigslist_ad(ad_url)
        title = obj['title']
        body = obj['body']
        city = self.get_city_from_url(ad_url)
        hash = hashlib.sha256(obj['body'].encode()).hexdigest()

        # If we've seen the hash, skip this ad
        if hash in hashes:
            # TODO: Probably reset the ads metadata to unused at this point
            print('Ad already in bucket')
            return False

        # Add hash to seen hashes and upload this ad
        metadata = {
            'url': ad_url,
            'hash': hash,
            'used': False,
            'word_count': len(body.split())
        }

        text = title + '\n' + body

        dir = city if not bucket_dir else bucket_dir
        destination_filepath = f'craigslist/{dir}/{title}.txt'
        upload_string_to_bucket('craig-the-poet', text, destination_filepath, metadata)

        hashes.append(hash)
        new_ledger = '\n'.join(hashes)
        upload_string_to_bucket('craig-the-poet', new_ledger, bucket_ledger)

        return True



    @LogDecorator()
    def scrape_ads_to_bucket(self, ad_list, count, bucket_dir=None):
        # TODO : Add abstraction via generator function to allow counts > one page of ads
        result_page = requests.get(ad_list)
        result_soup = BeautifulSoup(result_page.text, 'html.parser')

        # Scrape all ad URLs from ad list page
        urls = []
        for ad_title in result_soup.find_all('a', {'class':'result-title'}):
            urls.append(ad_title['href'])

        successful_uploads = 0
        for i, url in enumerate(urls):
            try:
                if self.scrape_ad_to_bucket(url, bucket_dir=bucket_dir):
                    successful_uploads += 1

                if successful_uploads >= count:
                    return
            except:
                pass



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
    def scrape_craigslist_ad(self, ad_url):
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
