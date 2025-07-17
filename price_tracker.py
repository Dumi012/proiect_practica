import time
import pyodbc
import schedule
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import smtplib
from email.mime.text import MIMEText
import pandas as pd
import matplotlib.pyplot as plt

PRODUCT_URLS = [
    'https://www.emag.ro/telefon-mobil-apple-iphone-13-128gb-5g-midnight-mlpf3rm-a/pd/DQFCMXMBM/',
    'https://www.emag.ro/telefon-mobil-samsung-galaxy-a16-dual-sim-128gb-4gb-ram-4g-black-sm-a165fzkbeue/pd/DVJ1YZYBM/',
    'https://www.emag.ro/telefon-mobil-samsung-galaxy-a56-dual-sim-8gb-ram-128gb-5g-awesome-graphite-sm-a566bzkaeue/pd/D1Z5X33BM/',
]

# Email configuration (edit these values)
EMAIL_SENDER = 'frasiladimitrie44@gmail.com'
EMAIL_PASSWORD = 'hcegnifdqksfcort'
EMAIL_RECIPIENT = 'imuducinalisarf@gmail.com'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587  # Usually 587 for TLS

DB_CONNECTION_STRING = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-F3VMQSE\\SQLEXPRESS;DATABASE=PriceTracker;Trusted_Connection=yes;'
CHECK_INTERVAL_MINUTES = 60


from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_db_connection():
    return pyodbc.connect(DB_CONNECTION_STRING)

def ensure_table_exists():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ProductPrices' AND xtype='U')
        CREATE TABLE ProductPrices (
            id INT IDENTITY PRIMARY KEY,
            url NVARCHAR(500) NOT NULL,
            title NVARCHAR(255),
            last_price DECIMAL(18,2),
            last_checked DATETIME DEFAULT GETDATE()
        )
    """)
    # Create PriceHistory table if it doesn't exist
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='PriceHistory' AND xtype='U')
        CREATE TABLE PriceHistory (
            id INT IDENTITY PRIMARY KEY,
            url NVARCHAR(500) NOT NULL,
            title NVARCHAR(255),
            price DECIMAL(18,2),
            checked_at DATETIME DEFAULT GETDATE()
        )
    """)
    conn.commit()
    conn.close()

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_title_and_price(driver, url):
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.page-title'))
        )
        title_elem = driver.find_element(By.CSS_SELECTOR, 'h1.page-title')
        title = title_elem.get_attribute("innerText").strip()
    except Exception as e:
        print("Eroare la extragerea titlului:", e)
        title = 'N/A'

    try:
        price_container = driver.find_element(By.CSS_SELECTOR, 'p.product-new-price')
        whole = price_container.get_property('innerText')
        price_text = whole.strip().replace('.', '').replace('Lei', '').replace(',', '.')
        price = float(price_text)
    except Exception as e:
        print("Eroare la extragerea prețului:", e)
        price = None

    return title, price



def get_last_price(url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT last_price FROM ProductPrices WHERE url = ?', url)
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def update_product(url, title, price):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM ProductPrices WHERE url = ?', url)
    row = cursor.fetchone()
    if row:
        cursor.execute('UPDATE ProductPrices SET title=?, last_price=?, last_checked=GETDATE() WHERE url=?', title, price, url)
    else:
        cursor.execute('INSERT INTO ProductPrices (url, title, last_price) VALUES (?, ?, ?)', url, title, price)
    conn.commit()
    conn.close()

def notify_price_change(url, title, old_price, new_price):
    print(f'Price change detected for {title}!')
    print(f'URL: {url}')
    print(f'Old price: {old_price}')
    print(f'New price: {new_price}')

    # Send email notification
    subject = 'Price Alert'
    body = f"""Price change detected for {title}!

URL: {url}
Old price: {old_price}
New price: {new_price}
"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECIPIENT

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        print('Email notification sent.')
    except Exception as e:
        print('Failed to send email notification:', e)

def insert_price_history(url, title, price):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO PriceHistory (url, title, price) VALUES (?, ?, ?)',
        url, title, price
    )
    conn.commit()
    conn.close()

def check_prices():
    print('Checking prices...')
    driver = get_driver()
    for url in PRODUCT_URLS:
        title, price = extract_title_and_price(driver, url)
        if price is None:
            print(f'Could not extract price for {url}')
            continue
        last_price = get_last_price(url)
        if last_price is not None and price != float(last_price):
            notify_price_change(url, title, last_price, price)
        update_product(url, title, price)
        insert_price_history(url, title, price)  # Store price history
    driver.quit()
    print('Check complete.')

def get_price_history(url):
    conn = get_db_connection()
    query = '''
        SELECT checked_at, price
        FROM PriceHistory
        WHERE url = ?
        ORDER BY checked_at
    '''
    df = pd.read_sql(query, conn, params=[url])
    conn.close()
    return df

def plot_price_history(df, url):
    if df.empty:
        print('No price history found for the given URL.')
        return
    plt.figure(figsize=(10, 5))
    plt.plot(df['checked_at'], df['price'], marker='o', linestyle='-')
    plt.title('Price Evolution')
    plt.xlabel('Checked At')
    plt.ylabel('Price (Lei)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid(True)
    plt.show()

def add_product_url():
    url = input('Enter the new product URL: ').strip()
    driver = get_driver()
    title, price = extract_title_and_price(driver, url)
    driver.quit()
    if price is None:
        print('Could not extract price for the given URL.')
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM ProductPrices WHERE url = ?', url)
    row = cursor.fetchone()
    if row:
        print('Product already exists in the database.')
    else:
        cursor.execute('INSERT INTO ProductPrices (url, title, last_price) VALUES (?, ?, ?)', url, title, price)
        conn.commit()
        print('Product added to ProductPrices.')
    cursor.execute('INSERT INTO PriceHistory (url, title, price) VALUES (?, ?, ?)', url, title, price)
    conn.commit()
    conn.close()
    if url not in PRODUCT_URLS:
        PRODUCT_URLS.append(url)
        print('Product URL added to tracking list.')

def delete_product_url():
    url = input('Enter the product URL to delete: ').strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ProductPrices WHERE url = ?', url)
    conn.commit()
    print('Product deleted from ProductPrices.')
    conn.close()
    if url in PRODUCT_URLS:
        PRODUCT_URLS.remove(url)
        print('Product URL removed from tracking list.')

def main():
    while True:
        print('\nPrice Tracker Menu:')
        print('1. Check prices now')
        print('2. Add a new product URL to track')
        print('3. Delete a tracked product')
        print('4. Show price history graph for a product URL')
        print('5. Exit')
        choice = input('Enter your choice (1-5): ').strip()
        if choice == '1':
            ensure_table_exists()
            check_prices()
        elif choice == '2':
            add_product_url()
        elif choice == '3':
            delete_product_url()
        elif choice == '4':
            url = input('Enter the product URL: ').strip()
            df = get_price_history(url)
            plot_price_history(df, url)
        elif choice == '5':
            print('Exiting program.')
            break
        else:
            print('Invalid choice. Please enter a number from 1 to 5.')

if __name__ == '__main__':
    main()
