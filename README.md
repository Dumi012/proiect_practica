# 🛒 Price Tracker – Aplicație de Monitorizare Prețuri cu Alerte Email și Grafic

Această aplicație Python rulează în terminal și îți permite să monitorizezi automat prețurile produselor de pe eMAG. Salvează datele în SQL Server, trimite email când se schimbă prețul și poate genera grafice cu istoricul prețului. Totul este controlat printr-un meniu simplu în terminal.

---

## ✅ Funcționalități

- Monitorizare automată a prețurilor pentru produse de pe eMAG
- Salvare în baza de date (`ProductPrices` și `PriceHistory`)
- Alerte email când prețul se modifică
- Vizualizare grafică a evoluției prețului
- Meniu interactiv în terminal: adăugare, ștergere, verificare, afișare grafic

---

## 🧱 Cerințe și Instalare

### 1. Instalarea pachetelor necesare

Pentru ca aplicația să funcționeze, are nevoie de câteva biblioteci externe. Acestea sunt listate într-un fișier numit `requirements.txt`.

```txt
selenium
pyodbc
schedule
webdriver-manager
pandas
matplotlib
