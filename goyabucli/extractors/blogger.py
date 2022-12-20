from typing import List
import requests
import re
import json
from goyabucli.utils import headers


class BloggerExtractor():
    def __init__(self):
        pass

    @staticmethod
    def parseUrl(url:str) -> List[str]:
        html = requests.get(url, headers=headers).text

        matches = re.findall(r'VIDEO_CONFIG = {.+streams\":(\[.+?\])', html)
        matches = list(filter(bool, matches))

        if not matches:
            return []
        
        streams = json.loads(matches[0])

        links = [stream['play_url'] for stream in streams]

        return links




