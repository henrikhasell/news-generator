import logging


logging.basicConfig(
    datefmt='%m/%d/%Y %I:%M:%S %p',
    format='%(asctime)s %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)
