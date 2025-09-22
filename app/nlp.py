"""NLP processing"""

import logging
from typing import Optional
import datetime
from dateparser.search import search_dates

logger = logging.getLogger(__name__)


class NLP:    
    def get_first_date_in_future(self, text: str) -> str:
        """Get first date in future
        
        Args:
            text: text to extract date from
            
        Returns:
            Date in future            
        """
        current_datetime = datetime.datetime.now()
        dates_res = search_dates(text, languages=['ru'])
        if dates_res is not None:
            if dates_res[0][1] < current_datetime:
                dates_res = search_dates(text, languages=['ru'], settings={'PREFER_DATES_FROM': 'future'})

            return dates_res[0][1].strftime('%Y-%m-%d')
        else:
            return None
