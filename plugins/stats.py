import json
import urllib
import urllib2
import time
from util import hook
import html
import re
from lxml import etree
import types


def db_init(db):
    print "In db_init function."
    # check to see that our db has the searches table and return a connection.
    #db.commit()
    #db.executescript("drop table if exists searches")
    try:
        db.execute("create table if not exists searches"
                   "(search_string UNIQUE PRIMARY KEY,link)")
    except db.Error as e:
        print "Error in db_init: " + str(e)
    #db.commit()

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
    #db.commit()
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
    #db.commit()
    return stub


def get_stats(stub):
    print "In get_stats function."
    stub = ''.join(stub)
    url = 'http://www.basketball-reference.com/players/' + stub
    handle = urllib2.urlopen(url)
    read = handle.read()
    results = etree.HTML(read)
    thelist = []
    floatcount = results.xpath('count(.//*[@id="per_game"]//tr[@class="full_table"][last()])')
    thecount = int(floatcount)
    strcount = str(thecount)
    print "Got " + strcount + " items."
    stats2 = results.xpath('.//*[@id="per_game"]//tr[@class="full_table"][last()]')
    statlist = []
    for i in stats2[0].iter():
        statlist.insert(len(statlist), i.text)
    print statlist
    print "Displaying results for the " + str(statlist[2]) + " season."
    return "Closing."


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
                #terms = find_player(inp)
                stub = store_link(db, output[0], output[1])
                output = get_stats(stub)
                return output
    except db.DatabaseError, e:
        print e
