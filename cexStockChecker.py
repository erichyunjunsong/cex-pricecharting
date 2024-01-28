from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import sqlite3
from bs4 import BeautifulSoup
import asyncio
import datetime

def setupDriver():
    options = Options()
    options.add_argument("start-maximized")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--enable-automation")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.headless = True
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def getListingsOnPage(pageNum):
    url = f'https://au.webuy.com/search?page={pageNum}&categoryIds=1018&categoryName=Switch+Software&sortBy=price_desc&availability=In+Stock+In+Store,In+Stock+Online'
    driver = setupDriver()
    driver.get(url)
    wait = WebDriverWait(driver, 30, 3)  # 30 seconds maximum wait time

    try:
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'content, no-results-list')))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()
        listings = soup.find_all('div', class_='content')
    except:
        return []
    return listings

def findListingName(listing):
    try:
        listingName = listing.find('div', class_= 'card-title').findChild().text
    except:
        listingName = ''
    return listingName

def findListingPrice(listing):
    try:
        listingPrice = listing.find('p', class_= 'product-main-price').text
    except:
        listingPrice = ''
    return listingPrice

def findListingStockStatus(listing):
    try:
        listing.find('span', class_= 'basket-container')
        listingStockStatus = True
    except:
        listingStockStatus = False
    return listingStockStatus

async def save_listing(title, price, currentDate):
    # Connect to the SQLite database
    conn = sqlite3.connect('listings.db')

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Create a table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price NUMBER,
            dateChecked DATE,
            inStock BOOLEAN
        )
    ''')

    # Insert the new listing into the table
    cursor.execute('INSERT INTO listings (title, price, dateChecked, inStock) VALUES (?, ?, ?, ?)', (title, price, currentDate, True))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

async def save_price(title, price, currentDate):
    # Connect to the SQLite database
    conn = sqlite3.connect('listings.db')

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Create a table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price NUMBER,
            dateChecked DATE
        )
    ''')

    # Insert the new listing into the table
    cursor.execute('INSERT INTO prices (title, price, dateChecked) VALUES (?, ?, ?)', (title, price, currentDate))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

async def is_new_listing(title):
    #catch instance where the database doesn't exist
    try: 
        conn = sqlite3.connect('listings.db')

        # Create a cursor object to execute SQL queries
        cursor = conn.cursor()

        # Check if the title exists in the database
        cursor.execute('SELECT title FROM listings WHERE title = ?', (title,))
        existing_title = cursor.fetchone()

        # Close the connection
        conn.close()

        # Return True if the title doesn't exist in the database (new listing)
        return not existing_title
    except:
        return True

async def set_in_stock(title, currentDate):
    # Connect to the SQLite database
    conn = sqlite3.connect('listings.db')

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Set listing as in stock
    cursor.execute('UPDATE listings SET inStock = TRUE WHERE title = ?', (title,))

    # Update dateCheck for listing
    cursor.execute('UPDATE listings SET dateChecked = ? WHERE title = ?', (currentDate, title,))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

async def check_stock(title):
    # Connect to the SQLite database
    conn = sqlite3.connect('listings.db')

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Check if title is in stock
    inStock = cursor.execute('SELECT inStock from listings WHERE title = ?', (title,))

    # Close the connection
    conn.close()

    return inStock

async def check_price_different(title, price):
    # Connect to the SQLite database
    conn = sqlite3.connect('listings.db')

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()


    currentSavedPrice = cursor.execute('SELECT price from listings WHERE title = ?', (title,))

    # Close the connection
    conn.close()
    
    # Check if price has changed
    if (currentSavedPrice != price):
        return False
    else:
        return True

async def get_sold(currentDate):
    # Connect to the SQLite database
    conn = sqlite3.connect('listings.db')

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Listings that were previously in stock but haven't been updated, means that they've recently been sold
    cursor.execute('SELECT title from listings WHERE inStock = TRUE AND dateChecked != ?', (currentDate,))

    sold = cursor.fetchall()

    # Commit the changes and close the connection
    conn.close()

    return sold

async def set_sold(currentDate):
    # Connect to the SQLite database
    conn = sqlite3.connect('listings.db')

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Set listings that weren't checked today as out of stock
    cursor.execute('UPDATE listings SET inStock = FALSE WHERE dateChecked != ?', (currentDate,))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

async def main():
    currentDate = datetime.datetime.now()
    newListings = []
    priceChangedListings = []
    pageNum = 1
    while(True):
        listings = getListingsOnPage(pageNum)
        if (listings == []):
            break
        for index in range (0, len(listings)):
            title = findListingName(listings[index])
            print(title)
            price = findListingPrice(listings[index])
            print(price)
            if await is_new_listing(title):
                await save_listing(title, price, currentDate)
                await save_price(title, price, currentDate)
                newListings.append({title,price})
            else:
                #check if out of stock first 
                if await check_stock(title) == False:
                    newListings.append([title,price])
                await set_in_stock(title, currentDate)
                if await check_price_different(title,price):
                    await save_price(title, price, currentDate)
                    priceChangedListings.append(title,price)

        pageNum += 1
    
    soldListings = await get_sold(currentDate)
    await set_sold(currentDate)
    print("New Listings")
    print(newListings)
    print("SOLD Listings")
    print(soldListings)
    print("Price change")
    print(priceChangedListings)
    return [newListings, soldListings]

if __name__ == "__main__":
    asyncio.run(main())