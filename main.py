import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def load_products():
    try:
        df = pd.read_csv("products.csv")
        print("[INFO] Produse încărcate cu succes.")
        return df
    except FileNotFoundError:
        print("[EROARE] Fișierul 'products.csv' nu a fost găsit.")
        return pd.DataFrame()

def check_website(url):
    # Deschide browserul și accesează pagina produsului (nu extrage încă prețul)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Nu deschide fereastră
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        print(f"[INFO] Accesat: {url}")
        time.sleep(3)
    except Exception as e:
        print(f"[EROARE] Nu s-a putut accesa pagina: {e}")
    finally:
        driver.quit()

def main():
    products = load_products()
    if products.empty:
        return

    for idx, row in products.iterrows():
        print(f"[INFO] Verific produs: {row['product_name']}")
        check_website(row['product_url'])

if __name__ == "__main__":
    main()
