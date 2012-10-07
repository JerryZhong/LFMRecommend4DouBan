# -*- coding=utf-8 -*- 

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from lxml import etree
import requests
import re
import datetime
import traceback

import sqlite3
import time

class HttpHelper:
  def __init__(self):
    self.conn = sqlite3.connect("html_cache.db")
    self.conn.text_factory = lambda x: unicode(x, 'utf-8', 'replace')  
    self.curs = self.conn.cursor()
    self.curs.execute('''CREATE TABLE if not exists htmls(url VARCHAR(255) UNIQUE, content TEXT, size INTEGER);''')
    self.conn.commit()
  
  def getCache(self, url):
    try:
      self.curs.execute("select * from htmls where url=?;" , (url,))
      row = self.curs.fetchone()
      
      result = str(row[1]).decode('utf-8')
      #print 'Cache Hit for %s' % url
      return result
    except:
      #traceback.print_exc()
      #print 'Cache Miss for %s' % url
      return None
  
  def updateCache(self, url, html):
    data = html.encode('utf-8')
    self.curs.execute("insert or replace into htmls values(?,?,?);", (url, data, len(data)))
    self.conn.commit()
  
  def close(self):
    self.conn.close()
  
  def cooldown(self, url):
    time.sleep(1)
  
  def get(self, url):
    html = self.getCache(url)
    if html: return html
    
    r = requests.get(url)
    html = r.text
    self.updateCache(url, html)
    return html


class DouBanUserFetcher:
  def __init__(self, httphelper, name=None, id=None):
    self.username = name
    self.userid = id
    self.httphelper = httphelper
  
  def getHtml(self, url):
    return self.httphelper.get(url)
  
  def mainpageUrl(self):
    return "http://book.douban.com/people/%s/" % (self.username or self.userid)
  
  def readingUrl(self):
    return self.mainpageUrl() + 'do'
  
  def readUrl(self):
    return self.mainpageUrl() + 'collect'
    
  def wishUrl(self):
    return self.mainpageUrl() + 'wish'
  
  def parseMainpage(self):
    url = self.mainpageUrl()
    htmltext = self.getHtml(url)
    
    dom = etree.HTML(htmltext)
    nodes = dom.xpath('//div[@id="db-book-mine"]/h2/span/a')
    
    intparsefun = lambda s : int(re.match(u"(\d+)本", s).group(1))
    
    self.readingCount = intparsefun(nodes[0].text)
    self.readCount = intparsefun(nodes[1].text)
    self.wishCount = intparsefun(nodes[2].text)
  
  def parseBooks(self, url):
    #print 'Fetch %s ...' % url
    htmltext = self.getHtml(url)
    
    dom = etree.HTML(htmltext)
    nodes = dom.xpath('//div[@class="item"]/div[@class="info"]')
    
    books = []
    for n in nodes:
      bookurl = n.xpath('.//li[@class="title"]/a')[0].get('href')
      
      bookid = int(re.search('/(\d+)/$', bookurl).group(1))
      booktitle = n.xpath('.//li[@class="title"]/a/em')[0].text
      
      datenode = n.xpath('.//li/span[@class="date"]')[0]
      adddate = datetime.datetime.strptime(datenode.text,'%Y-%m-%d')
      
      ratenode = [s for s in n.xpath('./ul/li[3]/span') if 'rating' in s.get('class')]
      rate = None
      if len(ratenode) > 0:
        rate = int(re.match('rating(\d)-t', ratenode[0].get('class')).group(1))
        
      tagnode = n.xpath('.//li/span[@class="tags"]')
      tags = []
      if len(tagnode) > 0:
        tags = tagnode[0].text[3:].split()
      
      description_node = [s for s in n.xpath('./ul/li') 
                             if len(s.attrib) == 0 and len(s.getchildren()) == 0]
      
      description = None
      if len(description_node) > 0:
        description = description_node[0].text.strip()
      
      books.append({'id' : bookid, 'title' : booktitle,
                    'rate' : rate, 'date': adddate,
                     'tags' : tags, 'description' : description})
    
    return books
  
  def getBookList(self, baseUrl, count):
    url = baseUrl
    books = self.parseBooks(url)
    
    while len(books) < count:
      books.extend(self.parseBooks(url+'?start=%s' % len(books)))
    
    return books
  
  def getReadBooks(self):
    return self.getBookList(self.readUrl(), self.readCount)
  
  def getReadingBooks(self):
    return self.getBookList(self.readingUrl(), self.readingCount)
  
  def getWishBooks(self):
    return self.getBookList(self.wishUrl(), self.wishCount)
  
  def getAllBooks(self):
    books = []
    
    books.extend(self.getReadBooks())
    books.extend(self.getReadingBooks())
    books.extend(self.getWishBooks())
    
    return books


class DouBanBookFetcher:
  def __init__(self, httphelper, id=None):
    self.bookid = id
    self.httphelper = httphelper
  
  def getHtml(self, url):
    return self.httphelper.get(url)
  
  def mainpageUrl(self):
    return "http://book.douban.com/subject/%s/" % self.bookid
  
  
  def readingUrl(self):
    return self.mainpageUrl() + 'doings'
  
  def readUrl(self):
    return self.mainpageUrl() + 'collections'
    
  def wishUrl(self):
    return self.mainpageUrl() + 'wishes'
  
  def parseMainpage(self):
    url = self.mainpageUrl()
    htmltext = self.getHtml(url)
    
    dom = etree.HTML(htmltext)
    node = dom.xpath('//div[@class="rating_wrap clearbox"]')[0]
    
    totalrate = float(node.xpath('./p[1]/strong')[0].text)
    
    percentparsefun = lambda s : float(re.match(r"([\d.]+)%", s).group(1))
    
    subnodes = [ s.strip() for s in node.xpath('./text()')]
    rateslist = [percentparsefun(s) / 100.0 for s in subnodes if s]
    rateCountDict = {5:rateslist[0], 4:rateslist[1], 3:rateslist[2], 2:rateslist[3], 1:rateslist[4] }
    
    return {'totalrate' : totalrate, 'rateCountDict' : rateCountDict}
  

    
httphelper = HttpHelper()

#fetcher = DouBanUserFetcher(httphelper, 'LockeS')
#fetcher.parseMainpage()
#fetcher.getAllBooks()

fetcher = DouBanBookFetcher(httphelper, '10769749')
fetcher.parseMainpage()

httphelper.close()


