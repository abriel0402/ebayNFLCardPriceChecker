import smtplib
import requests
from bs4 import BeautifulSoup
from PlayerCardDatabase import PLAYER_CARD_DATABASE
import schedule, time
from email.mime.text import MIMEText


def urlGenerator(player):
    url = "https://www.ebay.com/sch/i.html?_from=R40&_nkw=" + str(player["year"]) + "+" + player["cardType1"] + "+" + player["first"] + "+" + player["last"] + "+" + player["color"] + "+" + "PSA" + "+" + player["grade"] + "&_sacat=0&LH_BIN=1&_sop=15"
    return url


def getData(url):
    request = requests.get(url)
    soup = BeautifulSoup(request.text, "html.parser")
    return soup

def parse(soup):
    products = []
    results = soup.find_all("div", {"class": "s-item__info clearfix"})
    for item in results:
        title = item.find("span", {"role": "heading"})
        price_elem = item.find("span", {"class": "s-item__price"})
        shipping_elem = item.find("span", {"class": "s-item__shipping s-item__logisticsCost"})

        if title:
            title_text = title.text.strip()
        else:
            title_text = "N/A"

        if price_elem:
            price = price_elem.text.strip().replace("US $", "").replace(",", "")
        else:
            price = "N/A"

        if shipping_elem:
            shipping = shipping_elem.text.strip().replace("shipping", "")
        else:
            shipping = "N/A"

        link = item.find("a", {"class": "s-item__link"})["href"]

        if str(shipping) == "Free ":
            shipping = "0.00"

        product = {
            "title": title_text,
            "price": price,
            "shipping": shipping,
            "link": link,
        }
        products.append(product)
    
    if len(products) >= 2:
        return products[1]
    return products[0]

def parsePrice(priceStr):
    
    
    priceStr = priceStr.replace("$", "").replace(",", "")
    try:
        price = float(priceStr)
        return price
    except ValueError:
        return None

PREVIOUS_PRICES = {}

def sendEmail(subject, message):
    senderEmail = '#####@gmail.com'  
    senderPassword = '#####'  
    receiverEmail = '#####@gmail.com'  

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = senderEmail
    msg['To'] = receiverEmail

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(senderEmail, senderPassword)
        server.sendmail(senderEmail, receiverEmail, msg.as_string())
        server.quit()
        print('Email sent successfully.')
    except Exception as e:
        print('Email sending failed:', str(e))


def latestPriceCheck(url):
    soup = getData(url)
    product = parse(soup)
    return product

def main():
    for player in PLAYER_CARD_DATABASE:
        cardUrl = urlGenerator(player)
        latestPriceStr = latestPriceCheck(cardUrl)["price"]
        
        
        latestPrice = parsePrice(latestPriceStr)
        
        if latestPrice is not None:
            if cardUrl in PREVIOUS_PRICES:
                previousPrice = PREVIOUS_PRICES[cardUrl]
                priceChangePercentage = ((latestPrice - previousPrice) / previousPrice) * 100
                
                if (priceChangePercentage <= -35 and previousPrice >= 30.0) or (priceChangePercentage <= -60 and previousPrice <= 29.0):
                    subject = f"Price Drop Alert for {player['first']} {player['last']} Card"
                    message = f"The price of {player['first']} {player['last']} card has dropped by {priceChangePercentage:.2f}% to ${latestPrice:.2f}. \nLink: " + str(cardUrl) + "\n"
                    sendEmail(subject, message)
                    print("Email Sent!")
            
            print(str(latestPrice) + "   <---- " + player['first'] + " " + player["last"])
            

            PREVIOUS_PRICES[cardUrl] = latestPrice
            
        else:
            print(f"Unable to parse price for {player['first']} {player['last']} card: {latestPriceStr}")
    print("-----------------")
schedule.every(60).seconds.do(main)

while True:
    schedule.run_pending()
    time.sleep(1)