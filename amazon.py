import sys
import os
import requests
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from Levenshtein import distance

#convert all dash, & into space. Also remove stuff after '(' sign
def prepareString(inputStr):
    outputStr = inputStr.split('(')[0]
    outputStr = outputStr.replace('-', ' ')
    outputStr = outputStr.replace('&', ' ')
    outputStr = re.sub(' +', ' ', outputStr)
    return outputStr.lower()

#Filter out matching size and colors between Amazon and Sephora product title
def filterOutSizeAndColors(pTitle, pSize, colors):
    reducedTitle = pTitle
    if len(pSize) > 0:
        for word in pSize.split(' '):
            if word in reducedTitle:
                reducedTitle.replace(word, '')
        reducedTitle.strip()

    if len(colors) == 0: return reducedTitle
    beforeTitle = reducedTitle

    for color in colors.split('|'):
        color = color.strip()
        tempTitle = beforeTitle
        for word in color.split(' '):
            if word in tempTitle:
                tempTitle = tempTitle.replace(word, '')
                matched = True
        tempTitle = tempTitle.strip()
        if len(tempTitle) < len(reducedTitle):
            reducedTitle = tempTitle
    return reducedTitle.strip()

#Use Amazon Engine to search for targeted product. Find the best match among the first 3 results
def readSearchResults(brand, product, size, colors, driver, fo):
    url = 'http://www.amazon.com/s/?field-keywords=' + brand.replace(' ', '+') + '+' + product.replace(' ', '+')
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    maxMatch = -1
    if brand in product:
        originalStr = prepareString(product)
    else:
        originalStr = prepareString(brand + " " + product)

    for num in range(0, 4):
        productContainer = soup.find_all(attrs={'id': 'result_' + str(num)})
        if len(productContainer)==0: continue

        pTitleElement = productContainer[0].findAll(attrs={'class': 'a-size-medium a-color-null s-inline s-access-title a-text-normal'})
        if len(pTitleElement) == 0:
            pTitleElement = productContainer[0].findAll(attrs={'class': 'a-size-base a-color-null s-inline s-access-title a-text-normal'})
        if len(pTitleElement) > 0:
            pTitle = ''.join(pTitleElement[0].findAll(text=True))
            pTitle = pTitle.encode("utf8").strip(' \t\n\r')
            pTitle = filterOutSizeAndColors(pTitle, size, colors)
            tempStr = prepareString(pTitle)
            edit_dist = distance(tempStr, originalStr)
            matchValue = 100 - edit_dist*100 / len(originalStr)

            if (matchValue > maxMatch):
                maxMatch = matchValue
                linkElement = productContainer[0].findAll(attrs={'class': 'a-link-normal s-access-detail-page  a-text-normal'})
                productLink = linkElement[0]['href'].encode("utf8")

    pReviews = ''
    pColors = ''
    pTitle, pPrice, pInventory, pWeight, pStars = analyzeSearchProduct(productLink, driver)

    percentage_dist = "%.2f" % maxMatch
    fo.write(percentage_dist + "," + pTitle + "," + pPrice + "," + pInventory + "," + pWeight + "," + pReviews + ","
             + str(pStars) + "," + pColors + "\n")
    return

#Extract item weight from Amazon product details pane
def extractWeightFromDetailsPanel(soup):
    detailsPanel = soup.find_all(attrs={'id': 'detail-bullets'})
    if len(detailsPanel) == 0:
        detailsPanel = soup.find_all(attrs={'id': 'prodDetails'})
    if len(detailsPanel) == 0:
        detailsPanel = soup.find_all(attrs={'id': 'descriptionAndDetails'})
    soup2 = BeautifulSoup(str(detailsPanel[0]), "html.parser")

    #Remove all the scripts, and all href links
    [s.extract() for s in soup2('script')]
    [s.extract() for s in soup2('a')]
    textFields = soup2.find_all(attrs={'class': 'content'})
    if len(textFields) == 0:
        textFields = soup2.find_all(attrs={'id': 'detailBullets_feature_div'})

    weightStr = '';
    if len(textFields) == 0: return weightStr

    ulElement = textFields[0].findAll('ul')
    for li in ulElement[0].findAll('li'):
        if li.find('ul'):
            break
        lisStr = li.encode("utf8").lower()
        tempStr = lisStr.split('item weight:')
        if len(tempStr) > 1:
            tempStr = tempStr[1]
            tempStr = tempStr.split('</b>')[1]
            tempStr = tempStr.split('</li>')[0]
            weightStr = tempStr.replace("()", " ").strip()
            break;
    return weightStr

#Extract features from Amazon product page, including title, price, inventory, size/weight, reviews
def analyzeSearchProduct(productUrl, driver):
    productTitle = ''
    productPrice = ''
    inventoryString = ''
    starString = ''

    driver.get(productUrl)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    productTitle = soup.find_all(attrs={'id': 'productTitle'})
    productTitle = ''.join(productTitle[0].findAll(text=True))
    productTitle = productTitle.encode("utf8").strip(' \t\n\r')

    actionPanel = soup.find_all(attrs={'id': 'actionPanel'})
    if len(actionPanel) == 0:
        actionPanel = soup.find_all(attrs={'id': 'rightCol'})

    priceElement = actionPanel[0].findAll(attrs={'id': 'priceblock_ourprice'})
    if len(priceElement) > 0:
        productPrice = ''.join(priceElement[0].findAll(text=True))
        productPrice = productPrice.encode("utf8")
        inventoryElement = actionPanel[0].findAll(attrs={'id': 'availability'})
        inventoryString = ''.join(inventoryElement[0].findAll(text=True))
        inventoryString = str(inventoryString).strip(' \t\n\r')

    leftPanel = soup.find_all(attrs={'id': 'leftCol'})
    starElement = leftPanel[0].findAll(attrs={'class': 'a-icon a-icon-popover'})
    if len(starElement) > 0:
        starElement = starElement[0].parent
        starElement = starElement.findAll(attrs={'class': 'a-icon-alt'})
        starString = ''.join(starElement[0].findAll(text=True))
        starString = starString.encode("utf8")

    weightStr = '';
    sectionContent = leftPanel[0].findAll(attrs={'id': 'fbExpandableSectionContent'})
    if len(sectionContent) > 0:
        spanList = sectionContent[0].findAll(attrs={'class': 'a-list-item'})
        for span in spanList:
            liText = ''.join(span.findAll(text=True)).encode("utf8").strip().lower()
            sizeBlock = liText.split('size ')
            if len(sizeBlock)>1:
                weightStr = sizeBlock[1]

    if len(weightStr) == 0:
        weightStr = extractWeightFromDetailsPanel(soup)

    return productTitle, productPrice, inventoryString, weightStr, starString


def main():
    startAt = 0
    endAt = 30
    print 'Amazon product comparison, extract features from each product page, startAt=' + str(startAt) + ', endAt=' + str(endAt)

    chromedriver = "/Users/Khanh/tools/chromedriver"
    os.environ["webdriver.chrome.driver"] = chromedriver
    chop = webdriver.ChromeOptions()
    chop.add_extension("/Users/Khanh/tools/adblockplus-1.9.1.crx")
    driver = webdriver.Chrome(chromedriver, chrome_options=chop)

    fo = open('amazonResults.txt', 'w+')
    fi = open('analyzeResults.txt', 'r')
    fo.write("Match percenage,Title,Price,Inventory Count,Size,Reviews,Stars,Colors \n")
    line = fi.readline()
    line = fi.readline()
    currentCount = 0

    while line:
        words = line.split(',')
        brand = words[0]
        product = words[1]
        size = words[3]
        colors = words[7]
        if currentCount >= startAt:
            readSearchResults(brand, product, size, colors, driver, fo)

        currentCount += 1
        if currentCount > endAt: break
        line = fi.readline()

    fi.close()
    fo.close()
    driver.close()

# this is the standard boilerplate
if __name__ == '__main__':
    main()