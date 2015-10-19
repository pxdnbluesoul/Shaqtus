import json
import urllib
import urllib2
import time
from util import hook
import html
import re
from lxml import etree

@hook.command
def stats(inp):
    ".stats <player> -- Search Basketball Reference for player stats. Last logged year, per-game. Use .per36, .per100, .statsbyyear or .advanced for other stats."

    inp = urllib.quote_plus(inp)
    url = "http://www.basketball-reference.com/search/search.fcgi?search=" + inp
    handle = urllib2.urlopen(url)
    read = handle.read()
    results = etree.HTML(read)
    thelist = []
    floatcount = results.xpath('count(.//*[@id="players"]/div[@class="search-item"]/div[@class="search-item-name"]/a)')
    thecount = int(floatcount)
    strcount = str(thecount)
    print thecount
    if thecount > 1:
        output = ""
        for elem in results.findall('.//*[@id="players"]/div[@class="search-item"]/div[@class="search-item-name"]'):
            output += "Returned " + strcount + " results. Did you mean: "
            for i in elem.getchildren():
                print i.text
                thelist.insert(len(thelist),i.text)
        try:
            thelist.remove('All-Star')
            thelist.remove('Hall of Fame')
        except:
            pass
        years = re.compile("\s\(\d{4}\-\d{4}\)|\s\(\d{4}\)")
        thestring = ", ".join(thelist)
        thenewlist = years.sub("",thestring)
        output += thenewlist + "?"
    elif thecount == 1:
        output = "One Player Matched"
    else:
        output = "No results found."
    return output
