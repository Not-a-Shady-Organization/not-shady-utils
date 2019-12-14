import logging

LOG_FILEPATH = 'log.txt'
logging.basicConfig(filename=LOG_FILEPATH, level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info('Script beginning')

from google_utils import find_entities

text = "Text is a very interesting medium."
find_entities(text)

logger.info('Ending script')
