import json
import urllib
import urllib2
import time
from util import hook
import html
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
    except db.Error as e:
        print "Error in get_link: " + str(e)
    print "Printing row in get_link"
    print row
    print "Contents of inp.lower():" + str(inp)
    return row



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


def get_stats(stub):
    print "In get_stats function."
    stub = ''.join(stub)
    url = 'http://www.basketball-reference.com/players/' + stub
    handle = urllib2.urlopen(url)
    read = handle.read()
    results = etree.HTML(read)
    name = results.xpath('.//*[@id="info_box"]/h1')
    namefield = []
    if not name:  # Sometimes the name isn't where we expect it to be.
        name = results.xpath('.//*[@id="info_box"]/div[3]/h1')  # Usually that means it's here.
    for x in name[0].iter():
        namefield.insert(len(namefield), x.text)
    stats2 = results.xpath('.//*[@id="per_game"]//tr[@class="full_table"][last()]')
    statlist = []
    for i in stats2[0].iter():
        statlist.insert(len(statlist), i.text)
    try:
        statlist.remove(u'\xa0\u2605')  # Remove all-star designation
    except:
        pass
    if statlist[4] == "TOT":             # If a player played for more than 1 team
        statlist[5] = "Multiple Teams"   # Indicate as such in the proper spot
        statlist.insert(6, None)         # And add a blank entry to match the rest of the players.
    print statlist
    formatted = ("| " + namefield[0] + " | " + str(statlist[2]) + " | " + str(statlist[5]) + " | " + str(statlist[9]) + " GP | " +
                 str(statlist[10]) + " GS | " + str(statlist[11]) + " MPG | " + str(statlist[12]) + " FGM | " +
                 str(statlist[13]) + " FGA | " + str(statlist[14]) + " FG% | " + str(statlist[15]) + " 3PM | " +
                 str(statlist[16]) + " 3PA | " + str(statlist[17]) + " 3P% | " + str(statlist[22]) + " FTM | " +
                 str(statlist[23]) + " FTA | " + str(statlist[24]) + " FT% | " + str(statlist[25]) + " ORB | " +
                 str(statlist[26]) + " DRB | " + str(statlist[27]) + " RPG | " + str(statlist[28]) + " APG | " +
                 str(statlist[29]) + " SPG | " + str(statlist[30]) + " BPG | " + str(statlist[31]) + " TOV | " +
                 str(statlist[32]) + " PF | " + str(statlist[33]) + " PPG |")
    return formatted


def find_player(inp):
    print "In find_player function."
    inp = urllib.quote_plus(inp)
    url = "http://www.basketball-reference.com/search/search.fcgi?search=" + inp
    handle = urllib2.urlopen(url)
    read = handle.read()
    results = etree.HTML(read)
    thelist = []
    floatcount = results.xpath('count(.//*[@id="players"]/div[@class="search-item"]/div[@class="search-item-name"]/a)')
    thecount = int(floatcount)
    strcount = str(thecount)
    print "results in find_player: " + strcount
    if thecount > 1:
        print "Thecount > 1."
        output = "Returned " + strcount + " results. Did you mean: "
        for elem in results.findall('.//*[@id="players"]/div[@class="search-item"]/div[@class="search-item-name"]'):
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
        return output
    elif thecount == 1:
        print "thecount == 1"
        i = results.xpath('.//*[@id="players"]/div[@class="search-item"]/div[@class="search-item-name"]/a/@href')
        i = ''.join(i)
        i = i.lstrip("/players/")
        output = i + "|" + inp
        output = output.split("|")
        return output # Return a list
    else:
        output = "No results found."
        return output


@hook.command
def stats(inp, db=None):
    ".stats <player> -- Search Basketball Reference for player stats. Last logged year, per-game. Use .per36, .per100, .statsbyyear or .advanced for other stats."

    print "In stats function."
    db_init(db)
    try:
        row = get_link(db, inp)
        if row is not None:
            print "Contents of row: "
            print row
            output = get_stats(row)
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
                    output = get_stats(stub)
                    return output
                else:
                     print "Regex failed on " + str(output[0])
                     raise LookupError('Bad Link from BBall-Ref')
    except LookupError as e:
        print e
        return "Basketball Reference gave a bad link. Manual addition via .addlink needed."


@hook.command
def addlink(inp, nick='', db=None):
    ".addlink <shortened link to bball-ref page> <search terms> -- Force an insert to the database to add a link to a player page."

    if nick in administrators:
        arglist = inp.split(':', 1)
        stub = store_link(db, arglist[0], urllib.quote_plus(arglist[1]))
        return "Stored " + stub + " for term " + arglist[1]
    else:
        return "Only bot administrators can run that command."

@hook.command
def removelink(inp, nick='', db=None):
    ".removelink <search terms> -- Remove a bad link from the database."

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
