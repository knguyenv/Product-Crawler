import sys
import os
import requests

from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from selenium import webdriver

#Find all category links according to level 1 to 3
def FindCategory(level):
    r = requests.get('http://www.sephora.com/')
    soup = BeautifulSoup(r.text, "html.parser")
    header_html = soup.find_all(attrs={'class': 'Header'})

    soup2 = BeautifulSoup(str(header_html[0]), "html.parser")
    if level==3: linkClass = "Nav-link"
    else: linkClass = "meganav__link"
    links = soup2.findAll('a', linkClass)
    return links

def FindProductsInOneCategory(categoryLink, file, driver):
    url = 'http://www.sephora.com' + categoryLink['href'] + '?pageSize=-1'
    driver.get(url)
    soup = BeautifulSoup(driver.page_source , 'html.parser')
    productDiv = soup.find_all(attrs={'class': 'search-results'})
    if len(productDiv)==0:
        return

    soup2 = BeautifulSoup(str(productDiv[0]), "html.parser")
    productLinks = soup2.findAll('a')
    file.write("\n%d: %s \n" % (len(productLinks), url))
    for link in productLinks:
        file.write(link['href'] + "\n")


def main():
    print 'Sephora website, showing only Meganav_link (1st level category)'
    categoryLinks = FindCategory(3)

    chromedriver = "/Users/Khanh/tools/chromedriver"
    os.environ["webdriver.chrome.driver"] = chromedriver
    driver = webdriver.Chrome(chromedriver)

    file = open('sephoraProducts.txt', 'w+')
    for index in range(0, len(categoryLinks), 1):
        FindProductsInOneCategory(categoryLinks[index], file, driver)
    file.close()
    driver.close()


# this is the standard boilerplate
if __name__ == '__main__':
    main()