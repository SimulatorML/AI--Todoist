"""NLP processing based on natasha library"""

import logging
from typing import Optional
import datetime
from natasha import (
    MorphVocab,
    DatesExtractor,
)

logger = logging.getLogger(__name__)


class NLP:    
    def __init__(self):
        """Initialize the Todoist client with an API token."""
        self.morph_vocab = MorphVocab()
        self.dates_extractor = DatesExtractor(self.morph_vocab)

    
    def get_first_date_in_future(self, text: str) -> str:
        """Get first date in future
        
        Args:
            text: text to extract date from
            
        Returns:
            Date in future            
        """
        matches = self.dates_extractor(text)
        dates = [i.fact.as_json for i in matches]
        
        if dates:
            current_date = datetime.date.today()
            current_year = current_date.year

            if dates[0].get('year') == None:
                year = current_year
            else: 
                year = dates[0].get('year')

            specific_datetime = datetime.date(year, dates[0].get('month'), dates[0].get('day')) 

            if current_date > specific_datetime:
                specific_datetime = specific_datetime.replace(year=current_year + 1)

            return specific_datetime.strftime('%Y-%m-%d')
        else:
            return None
