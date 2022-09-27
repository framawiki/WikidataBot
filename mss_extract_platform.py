# Copyright (c) 2022 Facenapalm
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



# Add platform (P400) qualifier to Microsoft Store ID (P5885) claims.
# 
# See also:
# 
#    https://www.wikidata.org/wiki/Wikidata:Database_reports/Constraint_violations/P5885#"Mandatory_Qualifiers"_violations

import pywikibot
from pywikibot import pagegenerators as pg
import urllib.request
import http.client
import time
import sys
import re
import random

QUERY = """
SELECT DISTINCT ?item {
    ?item p:P5885 ?s
    FILTER NOT EXISTS { ?s pq:P400 [] }
}
"""

def get_platforms(store_id):
    attempts = 3
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
        "Accept-Encoding": "none",
        "Accept-Language": "en-US,en;q=0.8",
        "Connection": "keep-alive"
    }
    url = "https://www.microsoft.com/en-us/p/-/{}".format(store_id)
    for attempt_no in range(attempts):
        try:
            time.sleep(random.randint(1, 3))
            request = urllib.request.Request(url, None, headers)
            response = urllib.request.urlopen(request)
            html = response.read().decode("utf-8")
        except http.client.IncompleteRead as error:
            html = error.partial.decode("utf-8")
            print("{}: WARNING: partial read".format(store_id))
        except urllib.error.HTTPError as error:
            if error.code == 404:
                html = ""
            else:
                raise error
        except Exception as error:
            if attempt_no == (attempts - 1):
                raise error

    return re.findall(r"<svg .*?</svg>(PC|Xbox One|Xbox Series X\|S)", html)


def main():
    repo = pywikibot.Site()
    platform_items = {
        "PC": pywikibot.ItemPage(repo, "Q1406"),
        "Xbox One": pywikibot.ItemPage(repo, "Q13361286"),
        "Xbox Series X|S": pywikibot.ItemPage(repo, "Q98973368"),
    }
    generator = pg.WikidataSPARQLPageGenerator(QUERY, site=repo)
    for item in generator:
        if "P5885" not in item.claims:
            continue

        for i, claim in enumerate(item.claims["P5885"]):
            store_id = claim.getTarget()
            if "P400" in claim.qualifiers:
                print("{}: already has a qualifier".format(store_id))
                continue
            platforms = get_platforms(store_id)
            if platforms == []:
                print("{}: can't get platforms".format(store_id))
                continue
            for platform in platforms:
                qualifier = pywikibot.Claim(repo, "P400")
                qualifier.setTarget(platform_items[platform])
                claim.addQualifier(qualifier, summary="Adding qualifier to Microsoft Store ID `{}`".format(store_id))
                print("{}: platform set to {}".format(store_id, platform))

if __name__ == "__main__":
    main()
