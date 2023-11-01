import uvicorn
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time
import re
from functools import lru_cache
import asyncio


app = FastAPI()

options = Options()
# options.headless = True
options.add_argument("--window-size=1920,1200")
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)

# Helper function to extract PNR data
@lru_cache
def extract_pnr_data(soup):
    pnr = soup.find('span', {'data-bind': 'text: pnr'}).text
    train_number = soup.find('span', {'data-bind': 'text: trainNumber'}).text
    train_name = soup.find('span', {'data-bind': 'text: trainName'}).text
    train_rating = soup.find('span', {'style': 'font-size:14px;'}).text
    departure_station = soup.select_one('.light-text-1 span:nth-of-type(1)').text
    departure_time = soup.find('span', {'data-bind': 'text: departureTime'}).text
    destination_station = soup.select_one('.light-text-1 span:nth-of-type(3)').text
    arrival_time = soup.find('span', {'data-bind': 'text: arrivalTime'}).text
    boarding_date = soup.find('span', {'data-bind': 'text: boardingDate'}).text
    reserved_class = soup.find('span', {'data-bind': 'text: reservedClass'}).text
    quota_type = soup.find('span', {'data-bind': 'text: quotaType'}).text
    expected_platform = soup.find('span', {'data-bind': 'text:expectedPlatform'}).text
    remarks = soup.find('span', {'data-bind': 'text: InformationMessage'}).text

    pnr_data = {
        "PNR": pnr,
        "Train Number": train_number,
        "Train Name": train_name,
        "Train Rating": train_rating,
        "Departure Station": departure_station,
        "Departure Time": departure_time,
        "Destination Station": destination_station,
        "Arrival Time": arrival_time,
        "Boarding Date": boarding_date,
        "Reserved Class": reserved_class,
        "Quota Type": quota_type,
        "Expected Platform": expected_platform,
        "Remarks": remarks
    }

    return pnr_data


# Helper function to extract passenger status
@lru_cache
def extract_passenger_status(soup):
    table = soup.find('table', {'class': 'table'})

    header_row = table.find('thead').find('tr')
    header_cells = header_row.find_all('th')
    column_names = [re.sub(r'\s+', ' ', header.get_text(strip=True)) for header in header_cells]

    data_rows = table.find('tbody').find_all('tr')

    table_data = []
    for row in data_rows:
        data_cells = row.find_all(['th', 'td'])
        row_data = [cell.get_text(strip=True) for cell in data_cells]
        table_data.append(row_data)

    table_data_transposed = list(zip(*table_data))

    data_dict = {}
    for i, column_name in enumerate(column_names):
        data_dict[column_name] = table_data_transposed[i]

    return data_dict

async def fetch_pnr_data(pnr_number):
    try:
        t = time.time()
        url = f"https://www.confirmtkt.com/pnr-status/{pnr_number}"
        url = url.encode('ascii', 'ignore').decode('unicode_escape')
        driver.get(url)

        # Reduce sleep time as needed
        await asyncio.sleep(0.1)  # Adjust the sleep time

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Reduce sleep time as needed
        await asyncio.sleep(0.1)  # Adjust the sleep time

        page_source = driver.page_source

        soup = BeautifulSoup(page_source, 'html.parser')

        pnr_data = extract_pnr_data(soup)
        passenger_status = extract_passenger_status(soup)

        combined_data = {"PNR_Data": pnr_data, "Passenger_Status": passenger_status}
        json_data = json.dumps(combined_data, indent=4)
        print(time.time() - t)
        return json_data

    except Exception as e:
        return {"error": str(e)}

@app.get("/get_pnr_data/{pnr_number}")
async def get_pnr_data_endpoint(pnr_number: str):
    json_data = await fetch_pnr_data(pnr_number)
    result = json.loads(json_data)
    return result

# Use asyncio to run FastAPI application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)






# @app.get("/get_pnr_data/{pnr_number}")
# async def get_pnr_data(pnr_number: str):
#     try:
#         t = time.time()
#
#         url = f"https://www.confirmtkt.com/pnr-status/{pnr_number}"
#         url = url.encode('ascii', 'ignore').decode('unicode_escape')
#         driver.get(url)
#
#         time.sleep(0.1)
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(0.1)
#
#         page_source = driver.page_source
#         # driver.quit()
#
#         soup = BeautifulSoup(page_source, 'html.parser')
#
#         pnr_data = extract_pnr_data(soup)
#         passenger_status = extract_passenger_status(soup)
#
#         combined_data = {"PNR_Data": pnr_data, "Passenger_Status": passenger_status}
#         json_data = json.dumps(combined_data, indent=4)
#
#         print(time.time() - t)
#
#         result = json.loads(json_data)
#         return result
#
#     except Exception as e:
#         return {"error": str(e)}
