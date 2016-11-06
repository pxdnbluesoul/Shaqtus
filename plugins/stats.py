import urllib
import urllib2
from util import hook
import re
from lxml import etree
import types

administrators = ["bluesoul"]  # Multiple nicks are separated by commas and delimited with quotes.


def db_init(db):
    print "In db_init function."
    try:
        db.execute("create table if not exists searches"
                   "(search_string UNIQUE PRIMARY KEY,link)")
    except db.Error as e:
        print "Error in db_init: " + str(e)
    return db


def get_link(db, inp):
    print "In get_link function."
    inp = urllib.quote_plus(inp)
    try:
        row = db.execute("select link from searches where"
                         " search_string=lower(?) limit 1",
                         (inp.lower(),)).fetchone()
        print "Printing row in get_link"
        print row
        print "Contents of inp.lower():" + str(inp)
        return row
    except db.Error as e:
        print "Error in get_link: " + str(e)


def store_link(db, stub, search):
    print "In store_link function."
    try:
        db.execute("insert into searches (search_string, link) VALUES (?, ?)", (search.lower(), stub))
    except db.Error as e:
        print "Error in store_link: " + str(e)
    return stub


def remove_link(db, search):
    print "In remove_link function."
    try:
        db.execute("delete from searches where search_string = ?", (search.lower(),))
        return True
    except db.Error as e:
        print "Error in remove_link: " + str(e)
        return False


def get_stats(stub, year, per, playoffs):
    print "In get_stats function."
    stub = ''.join(stub)
    url = 'http://www.basketball-reference.com/players/' + stub
    agent = 'Shaqtus/1.0'
    req = urllib2.Request(url, headers={'User-Agent': agent})
    handle = urllib2.urlopen(req)
    read = handle.read()
    read = read.replace("<!--", "")    # Everything but per-game is commented out
    read = read.replace("-->", "")     # for some stupid reason as of November 2016
    results = etree.HTML(read)
    name = results.xpath('.//h1')
    namefield = []
    if not name:  # Sometimes the name isn't where we expect it to be.
        name = results.xpath('.//*[@id="info_box"]/div[3]/h1')  # Usually that means it's here.
    for x in name[0].iter():
        namefield.insert(len(namefield), x.text)
    if playoffs is True:
        if per == "per36":
            if year is None:
                stats2 = results.xpath('.//*[@id="playoffs_per_minute"]//tr[@class="full_table"][last()]')
            elif year == "career":
                stats2 = results.xpath('.//*[@id="playoffs_per_minute"]/tfoot/tr[1]')
            else:
                stats2 = results.xpath('.//*[@id="playoffs_per_minute.' + year + '"]')
        elif per == "per100":
            if year is None:
                stats2 = results.xpath('.//*[@id="playoffs_per_poss"]//tr[@class="full_table"][last()]')
            elif year == "career":
                stats2 = results.xpath('.//*[@id="playoffs_per_poss"]/tfoot/tr[1]')
            else:
                stats2 = results.xpath('.//*[@id="playoffs_per_poss.' + year + '"]')
        elif per == "advanced":
            if year is None:
                stats2 = results.xpath('.//*[@id="playoffs_advanced"]//tr[@class="full_table"][last()]')
            elif year == "career":
                stats2 = results.xpath('.//*[@id="playoffs_advanced"]/tfoot/tr[1]')
            else:
                stats2 = results.xpath('.//*[@id="playoffs_advanced.' + year + '"]')
        else:
            if year is None:
                stats2 = results.xpath('.//*[@id="playoffs_per_game"]//tr[@class="full_table"][last()]')
            elif year == "career":
                stats2 = results.xpath('.//*[@id="playoffs_per_game"]/tfoot/tr[1]')
            else:
                stats2 = results.xpath('.//*[@id="playoffs_per_game.' + year + '"]')
    else:
        if per == "per36":
            if year is None:
                stats2 = results.xpath('.//*[@id="per_minute"]//tr[@class="full_table"][last()]')
            elif year == "career":
                stats2 = results.xpath('.//*[@id="per_minute"]/tfoot/tr[1]')
            else:
                stats2 = results.xpath('.//*[@id="per_minute.' + year + '"]')
        elif per == "per100":
            if year is None:
                stats2 = results.xpath('.//*[@id="per_poss"]//tr[@class="full_table"][last()]')
            elif year == "career":
                stats2 = results.xpath('.//*[@id="per_poss"]/tfoot/tr[1]')
            else:
                stats2 = results.xpath('.//*[@id="per_poss.' + year + '"]')
        elif per == "advanced":
            if year is None:
                stats2 = results.xpath('.//*[@id="advanced"]//tr[@class="full_table"][last()]')
            elif year == "career":
                stats2 = results.xpath('.//*[@id="advanced"]/tfoot/tr[1]')
            else:
                stats2 = results.xpath('.//*[@id="advanced.' + year + '"]')
        else:
            if year is None:
                stats2 = results.xpath('.//*[@id="per_game"]//tr[@class="full_table"][last()]')
            elif year == "career":
                stats2 = results.xpath('.//*[@id="per_game"]/tfoot/tr[1]')
            else:
                stats2 = results.xpath('.//*[@id="per_game.' + year + '"]')
    statlist = []
    print stats2
    for i in stats2[0].iter():
        statlist.insert(len(statlist), i.text)
    try:
        statlist.remove(u'\xa0\u2605')  # Remove all-star designation
    except ValueError:
        pass
    try:
        statlist.remove(u'\xa0\u274d')  # Remove championship designation
    except ValueError:
        pass
    if statlist[4] == "TOT":             # If a player played for more than 1 team
        statlist[5] = "Multiple Teams"   # Indicate as such in the proper spot
        statlist.insert(6, None)         # And add a blank entry to match the rest of the players.
    statlist = filter(None, statlist)    # Remove all blanks.
    print statlist
    if per == "advanced":
        if year == "career":
            formatted = (namefield[0] + " | " + str(statlist[0]) + " | " + str(statlist[4]) + " PER | " +
                         str(statlist[5]) + " TS% | " +
                         str(statlist[6]) + " 3PAr | " + str(statlist[7]) + " FTr | " + str(statlist[8]) + " ORB% | " +
                         str(statlist[9]) + " DRB% | " + str(statlist[10]) + " TRB% | " + str(statlist[11]) + " AST% | " +
                         str(statlist[12]) + " STL% | " + str(statlist[13]) + " BLK% | " + str(statlist[14]) + " TOV% | " +
                         str(statlist[15]) + " USG% | " + str(statlist[16]) + " OWS | " + str(statlist[17]) + " DWS | " +
                         str(statlist[18]) + " WS | " + str(statlist[19]) + " WS/48 | " + str(statlist[20]) + " OBPM | " +
                         str(statlist[21]) + " DBPM | " + str(statlist[22]) + " BPM | " + str(statlist[23]) + " VORP")
        else:
            formatted = (namefield[0] + " | " + str(statlist[1]) + " | " + str(statlist[7]) + " PER | " +
                         str(statlist[8]) + " TS% | " +
                         str(statlist[9]) + " 3PAr | " + str(statlist[10]) + " FTr | " + str(statlist[11]) + " ORB% | " +
                         str(statlist[12]) + " DRB% | " + str(statlist[13]) + " TRB% | " + str(statlist[14]) + " AST% | " +
                         str(statlist[15]) + " STL% | " + str(statlist[16]) + " BLK% | " + str(statlist[17]) + " TOV% | " +
                         str(statlist[18]) + " USG% | " + str(statlist[19]) + " OWS | " + str(statlist[20]) + " DWS | " +
                         str(statlist[21]) + " WS | " + str(statlist[22]) + " WS/48 | " + str(statlist[23]) + " OBPM | " +
                         str(statlist[24]) + " DBPM | " + str(statlist[25]) + " BPM | " + str(statlist[26]) + " VORP")
    elif per == "per100":
        if year == "career":
            formatted = (namefield[0] + " | " + str(statlist[0]) + " | " + str(statlist[2]) + " GP | " +
                         str(statlist[3]) + " GS | " + str(statlist[4]) + " MP | " + str(statlist[5]) + " FGM | " +
                         str(statlist[6]) + " FGA | " + str(statlist[7]) + " FG% | " + str(statlist[8]) + " 3PM | " +
                         str(statlist[9]) + " 3PA | " + str(statlist[10]) + " 3P% | " + str(statlist[14]) + " FTM | " +
                         str(statlist[15]) + " FTA | " + str(statlist[16]) + " FT% | " + str(statlist[17]) + " ORB | " +
                         str(statlist[18]) + " DRB | " + str(statlist[19]) + " TRB | " + str(statlist[20]) + " AST | " +
                         str(statlist[21]) + " STL | " + str(statlist[22]) + " BLK | " + str(statlist[23]) + " TOV | " +
                         str(statlist[24]) + " PF | " + str(statlist[25]) + " PTS | " + str(statlist[26]) + " ORtg | " +
                         str(statlist[27]) + " DRtg")
        else:
            formatted = (namefield[0] + " | " + str(statlist[0]) + " | " + str(statlist[5]) + " GP | " +
                         str(statlist[6]) + " GS | " + str(statlist[7]) + " MP | " + str(statlist[8]) + " FGM | " +
                         str(statlist[9]) + " FGA | " + str(statlist[10]) + " FG% | " + str(statlist[11]) + " 3PM | " +
                         str(statlist[12]) + " 3PA | " + str(statlist[13]) + " 3P% | " + str(statlist[17]) + " FTM | " +
                         str(statlist[18]) + " FTA | " + str(statlist[19]) + " FT% | " + str(statlist[20]) + " ORB | " +
                         str(statlist[21]) + " DRB | " + str(statlist[22]) + " TRB | " + str(statlist[23]) + " AST | " +
                         str(statlist[24]) + " STL | " + str(statlist[25]) + " BLK | " + str(statlist[26]) + " TOV | " +
                         str(statlist[27]) + " PF | " + str(statlist[28]) + " PTS | " + str(statlist[29]) + " ORtg | " +
                         str(statlist[30]) + " DRtg")
    elif per == "per36":
        if year == "career":
            formatted = (namefield[0] + " | " + str(statlist[0]) + " | " + str(statlist[2]) + " GP | " +
                         str(statlist[3]) + " GS | " + str(statlist[4]) + " MP | " + str(statlist[5]) + " FGM | " +
                         str(statlist[6]) + " FGA | " + str(statlist[7]) + " FG% | " + str(statlist[8]) + " 3PM | " +
                         str(statlist[9]) + " 3PA | " + str(statlist[10]) + " 3P% | " + str(statlist[14]) + " FTM | " +
                         str(statlist[15]) + " FTA | " + str(statlist[16]) + " FT% | " + str(statlist[17]) + " ORB | " +
                         str(statlist[18]) + " DRB | " + str(statlist[19]) + " TRB | " + str(statlist[20]) + " AST | " +
                         str(statlist[21]) + " STL | " + str(statlist[22]) + " BLK | " + str(statlist[23]) + " TOV | " +
                         str(statlist[24]) + " PF | " + str(statlist[25]) + " PTS")
        else:
            formatted = (namefield[0] + " | " + str(statlist[0]) + " | " + str(statlist[2]) + " | " +
                         str(statlist[5]) + " GP | " +
                         str(statlist[6]) + " GS | " + str(statlist[7]) + " MP | " + str(statlist[8]) + " FGM | " +
                         str(statlist[9]) + " FGA | " + str(statlist[10]) + " FG% | " + str(statlist[11]) + " 3PM | " +
                         str(statlist[12]) + " 3PA | " + str(statlist[13]) + " 3P% | " + str(statlist[17]) + " FTM | " +
                         str(statlist[18]) + " FTA | " + str(statlist[19]) + " FT% | " + str(statlist[20]) + " ORB | " +
                         str(statlist[21]) + " DRB | " + str(statlist[22]) + " TRB | " + str(statlist[23]) + " AST | " +
                         str(statlist[24]) + " STL | " + str(statlist[25]) + " BLK | " + str(statlist[26]) + " TOV | " +
                         str(statlist[27]) + " PF | " + str(statlist[28]) + " PTS")
    else:
        if year == "career":
            formatted = (namefield[0] + " | " + str(statlist[0]) + " | " + str(statlist[2]) + " GP | " +
                         str(statlist[3]) + " GS | " + str(statlist[4]) + " MPG | " + str(statlist[5]) + " FGM | " +
                         str(statlist[6]) + " FGA | " + str(statlist[7]) + " FG% | " + str(statlist[8]) + " 3PM | " +
                         str(statlist[9]) + " 3PA | " + str(statlist[10]) + " 3P% | " + str(statlist[15]) + " FTM | " +
                         str(statlist[16]) + " FTA | " + str(statlist[17]) + " FT% | " + str(statlist[18]) + " ORB | " +
                         str(statlist[19]) + " DRB | " + str(statlist[20]) + " TRB | " + str(statlist[21]) + " APG | " +
                         str(statlist[22]) + " SPG | " + str(statlist[23]) + " BPG | " + str(statlist[24]) + " TOV | " +
                         str(statlist[25]) + " PF | " + str(statlist[26]) + " PPG")
        else:
            formatted = (namefield[0] + " | " + str(statlist[0]) + " | " + str(statlist[2]) + " | " +
                         str(statlist[5]) + " GP | " +
                         str(statlist[6]) + " GS | " + str(statlist[7]) + " MPG | " + str(statlist[8]) + " FGM | " +
                         str(statlist[9]) + " FGA | " + str(statlist[10]) + " FG% | " + str(statlist[11]) + " 3PM | " +
                         str(statlist[12]) + " 3PA | " + str(statlist[13]) + " 3P% | " + str(statlist[18]) + " FTM | " +
                         str(statlist[19]) + " FTA | " + str(statlist[20]) + " FT% | " + str(statlist[21]) + " ORB | " +
                         str(statlist[22]) + " DRB | " + str(statlist[23]) + " RPG | " + str(statlist[24]) + " APG | " +
                         str(statlist[25]) + " SPG | " + str(statlist[26]) + " BPG | " + str(statlist[27]) + " TOV | " +
                         str(statlist[28]) + " PF | " + str(statlist[29]) + " PPG")
    return formatted


def find_player(inp):
    print "In find_player function."
    inp = urllib.quote_plus(inp)
    url = "http://www.basketball-reference.com/search/search.fcgi?search=" + inp
    handle = urllib2.urlopen(url)
    read = handle.read()
    results = etree.HTML(read)
    thelist = []
    floatcount = results.xpath('count(.//*[@id="players"]/div[@class="search-item"]/div[@class="search-item-name"]//a)')
    thecount = int(floatcount)
    strcount = str(thecount)
    print "results in find_player: " + strcount
    if thecount > 1:
        print "Thecount > 1."
        output = "Returned " + strcount + " results. Did you mean: "
        for elem in results.findall('.//*[@id="players"]//div[@class="search-item-name"]'):
            for i in elem.iter(tag="a"):
                print i.text
                thelist.insert(len(thelist), i.text)
        # try:
        #     thelist.remove('All-Star')
        #     thelist.remove('Hall of Fame')
        # except ValueError:
        #     pass
        years = re.compile("\s\(\d{4}\-\d{4}\)|\s\(\d{4}\)")
        thestring = ", ".join(thelist)
        thenewlist = years.sub("", thestring)
        output += thenewlist + "?"
        return output
    elif thecount == 1:
        print "thecount == 1"
        i = results.xpath('.//*[@id="players"]/div[@class="search-item"]/div[@class="search-item-name"]//a/@href')
        print "results.xpath: " + str(i)
        i = ''.join(i)
        print "after join: " + i
        i = re.sub('/players/', '', i)
        print "after lstrip: " + i
        output = i + "|" + inp
        print "output: " + output
        output = output.split("|")
        return output  # Return a list
    else:
        output = "No results found."
        return output


@hook.command
def stats(inp, db=None):
    """.stats <player> [per36|per100|advanced] [playoffs] [career|4-digit year] -- Search Basketball Reference for player stats. Default is last logged year, per-game."""

    print "In stats function."
    db_init(db)

    yearmatch = re.search('(\d\d\d\d)', inp)
    year = None  # Prepping for get_stats if no year set. Defaults to most recent.
    if yearmatch:
        year = yearmatch.group(0)
        print "Year: " + year
        inp = re.sub('(\s\d\d\d\d)', '', inp)

    per36match = re.search('(per36)', inp)
    per = None
    if per36match:
        per = "per36"
        inp = re.sub('\sper36', '', inp)
    per100match = re.search('(per100)', inp)
    if per100match:
        if per == "per36":
            return "You can't run per36 and per100 at the same time."
        else:
            per = "per100"
            inp = re.sub('\sper100', '', inp)
    advancedmatch = re.search('(advanced)', inp)
    if advancedmatch:
        if (per == "per36") or (per == "per100"):
            return "Cannot mix advanced stats with per36 or per100"
        else:
            per = "advanced"
            inp = re.sub('\sadvanced', '', inp)

    playoffs = False
    playoffsmatch = re.search('(playoffs)', inp)
    if playoffsmatch:
        playoffs = True
        inp = re.sub('\splayoffs', '', inp)

    careermatch = re.search('(career)', inp)
    if careermatch:
        if year is not None:
            return "Cannot search for career and year at the same time."
        else:
            year = "career"
            inp = re.sub('\scareer', '', inp)

    try:
        row = get_link(db, inp)
        if row is not None:
            print "Contents of row: "
            print row
            output = get_stats(row, year, per, playoffs)
            return output
        else:
            output = find_player(inp)
            if isinstance(output, types.StringTypes):
                if output == "No results found.":
                    return output
                elif output.find("Returned") is not -1:
                    return output
            else:
                print output
                if re.match("\w/\w", output[0]) is not None:
                    stub = store_link(db, output[0], output[1])
                    output = get_stats(stub, year, per, playoffs)
                    return output
                else:
                    print "Regex failed on " + str(output[0])
                    raise LookupError('Bad Link from BBall-Ref')
    except LookupError as e:
        print e
        return "Lookup failed."


@hook.command
def addlink(inp, nick='', db=None):
    """.addlink <shortened link to bball-ref page>:<search terms> -- Manually add player link. e.g., .addlink o/onealsh01.html:shaq"""

    if nick in administrators:
        arglist = inp.split(':', 1)
        stub = store_link(db, arglist[0], urllib.quote_plus(arglist[1]))
        return "Stored " + stub + " for term " + arglist[1]
    else:
        return "Only bot administrators can run that command."


@hook.command
def removelink(inp, nick='', db=None):
    """.removelink <search terms> -- Remove a bad link from the database. e.g., .removelink shaq"""

    if nick in administrators:
        result = remove_link(db, urllib.quote_plus(inp))
        if result is True:
            return "Removed " + inp + " successfully."
        elif result is False:
            return inp + " is not in database."
        else:
            return "Something bad happened. No response from remove_link() call."
    else:
        return "Only bot administrators can run that command."
