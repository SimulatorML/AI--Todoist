"""NLP processing"""

import logging
from typing import Optional
import datetime
from natasha import (
    MorphVocab,
    DatesExtractor,
)
from dateparser.search import search_dates

logger = logging.getLogger(__name__)


class NLP:    
    def __init__(self):
        """Initialize the library"""
        self.morph_vocab = MorphVocab()
        self.dates_extractor = DatesExtractor(self.morph_vocab)

    
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

        # пытаемся вытащить дату по-другому
        matches = self.dates_extractor(text)
        dates = [i.fact.as_json for i in matches]
        
        if dates:
            current_date = datetime.date.today()
            current_year = current_date.year
            current_month = current_date.month
            current_day = current_date.day

            if dates[0].get('year') == None:
                year = current_year
            else: 
                year = dates[0].get('year')

            if dates[0].get('month') == None:
                month = current_year
            else: 
                month = dates[0].get('month')

            if dates[0].get('day') == None:
                day = current_year
            else: 
                day = dates[0].get('day')

            found_datetime = datetime.date(year, month, day) 

            if current_date > found_datetime:
                found_datetime = found_datetime.replace(year=current_year + 1)

            return found_datetime.strftime('%Y-%m-%d')
        else:
            return None
