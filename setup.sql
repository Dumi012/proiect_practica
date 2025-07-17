CREATE DATABASE PriceTracker;
GO

USE PriceTracker;
GO

CREATE TABLE ProductPrices (
    id INT IDENTITY PRIMARY KEY,
    url NVARCHAR(500) NOT NULL,
    title NVARCHAR(255),
    last_price DECIMAL(18,2),
    last_checked DATETIME DEFAULT GETDATE()
);

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='PriceHistory' AND xtype='U')
BEGIN
    CREATE TABLE PriceHistory (
        id INT IDENTITY PRIMARY KEY,
        url NVARCHAR(500) NOT NULL,
        title NVARCHAR(255),
        price DECIMAL(18,2),
        checked_at DATETIME DEFAULT GETDATE()
    );
END
