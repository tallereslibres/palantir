################################################################
import os
import sys
import logging

import __main__

# Configure logging
log_format = "%(asctime)-15s %(message)s"
logging.basicConfig(filename="/home/debian/palantir/logs/palantir.log", format=log_format)
logger = logging.getLogger("palantir")
logger.setLevel(logging.DEBUG)

# Debug Print
def debugp(string):
    global DEBUG
    if DEBUG:
        print repr(string)



