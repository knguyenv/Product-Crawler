import sys
import os
import requests
import re

from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def analyzeProduct(link, driver, fo):
    url = 'http://www.sephora.com' + link
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    product_html = soup.find_all(attrs={'id': 'product-content'})
    if len(product_html) == 0: return
    brand = product_html[0]['data-brand'].encode("utf8")

    title_html = product_html[0].findAll(attrs={'class': 'pdp-primary__title'})
    title = ''.join(title_html[0].find_all(text=True, recursive=False)).strip().encode("utf8")


    soup2 = BeautifulSoup(str(product_html[0]), "html.parser")
    price_html = soup2.find_all(attrs={'class': re.compile("(Price-list)+")})
    if len(price_html) > 0:
        price_html = price_html[0].findAll(text=True)
        #Check to see if there is any sales price
        sales_html = soup2.find_all(attrs={'class': re.compile("(Price-sale)+")})
        if len(sales_html) > 0:
            sales = ''.join(sales_html[0].findAll(text=True))
            sales = str(sales).strip(' \t\n\r')
            if len(sales)>1:
                price_html = sales_html[0].findAll(text=True)
        price = ''.join(price_html)
        price = str(price).strip(' \t\n\r')

    rating_html = soup2.find_all(attrs={'class': 'pdp-rating u-linkComplex'})
    if len(rating_html) > 0:
        reviews_html = rating_html[0].findAll(attrs={'class': 'u-linkComplexTarget'})
        reviews = ''.join(reviews_html[0].findAll(text=True))
        reviews = str(reviews).strip(' \t\n\r')
        stars_html = rating_html[0].findAll(attrs={'class': 'stars'})
        stars = stars_html[0]['seph-stars']

    size_html = soup2.find_all(attrs={'class': re.compile("(InfoRow-size)+")})
    if len(size_html) > 0:
        size_html = size_html[0].find_all(attrs={'class': re.compile("(InfoRow-value)+")})
        size = ''.join(size_html[0].findAll(text=True))
        size = str(size).strip(' \t\n\r')

    breadcrumb = ""
    breadcrumb_html = soup.find_all(attrs={'class': "Breadcrumb-link"})
    if len(breadcrumb_html) > 1:
        for item in breadcrumb_html[0:-1]:
            breadcrumb = breadcrumb + str(''.join(item.findAll(text=True))) + '>'

    colors = []
    colors_html = soup2.find_all(attrs={'class': re.compile("(SwatchGroup-selector)+")})
    if len(colors_html) > 0:
        colors_html = colors_html[0].find_all(attrs={'class': 'Swatch'})
        for item in colors_html:
            if 'data-analytics' in item.attrs:
                color = item['data-analytics'].encode("utf8").split(':')
                if len(color) == 2: colors.append(color[1])

    colors = '|'.join(sorted(colors))
    fo.write(brand + "," + title + "," + price + "," + size + "," + reviews + "," + str(stars) +
             "," + breadcrumb + "," + colors + "\n")
    #print brand + ", " + title + ", price: " + price + ", size: " + size + ", " + reviews + ", stars: " + str(stars) + ", " + breadcum
    return

def main():
    startAt = 0
    endAt = 30
    print 'Sephora website, extract features from each product page, startAt=' + str(startAt) + ', endAt=' + str(endAt)

    chromedriver = "/Users/Khanh/tools/chromedriver"
    os.environ["webdriver.chrome.driver"] = chromedriver
    chop = webdriver.ChromeOptions()
    chop.add_extension("/Users/Khanh/tools/adblockplus-1.9.1.crx")
    driver = webdriver.Chrome(chromedriver, chrome_options=chop)

    fo = open('analyzeResults.txt', 'w+')
    fi = open('sephoraProducts.txt', 'r')
    fo.write("Brand,Title,Price,Size,Reviews,Stars,Category,Colors \n")
    line = fi.readline()
    currentCount = 0

    while line:
        line = fi.readline()
        max = int(line.split(': ')[0])
        for num in range(0, max, 1):
            productUrl = fi.readline()
            if currentCount >= startAt:
                analyzeProduct(productUrl, driver, fo)
            currentCount += 1
            if currentCount >= endAt: break

        line = fi.readline()
        if currentCount >= endAt: break

    fi.close()
    fo.close()
    driver.close()

# this is the standard boilerplate
if __name__ == '__main__':
    main()