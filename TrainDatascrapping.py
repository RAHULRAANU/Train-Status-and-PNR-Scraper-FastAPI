import json
import uvicorn
from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
import pandas as pd
from fastapi.responses import JSONResponse
import time
from functools import lru_cache


app = FastAPI()

@lru_cache
def extract_train_data(soup):
    # Create an empty list to store data
    data = []


    for post in soup.find_all("div", class_="row rs__station-row flexy"):
        station = post.find_all("div", class_="col-xs-3")[0].get_text(strip=True)
        date = post.find_all("div", class_="col-xs-3")[1].get_text(strip=True, separator=" ")
        arrives = post.find_all("div", class_="col-xs-2")[0].get_text(strip=True)
        departs = post.find_all("div", class_="col-xs-2")[1].get_text(strip=True)
        late = post.find_all("div", class_="col-xs-2")[2].get_text(strip=True)

        # Appending the data in list
        data.append([station, date, arrives, departs, late])

    # Create a DataFrame from the list of data
    columns = ["Station", "Date", "Arrives", "Departs", "Late"]

    df = pd.DataFrame(data, columns=columns)

    # Convert DataFrame to JSON
    json_data = df.to_json(orient='records')

    # Output Json data
    data = json.loads(json_data)

    return data


@lru_cache
def fetch_train_data(TraiNo: str , journeyDate: str):
    try:
        # t = time.time()
        # Url for train status scrapping
        Url = f"https://www.confirmtkt.com/train-running-status/{TraiNo}?Date={journeyDate}"

        # Send a GET request to the user-provided URL
        response = requests.get(Url)

        # Check if the request was successful
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        fdata = extract_train_data(soup)

        # Convert the list of dictionaries to JSON format
        json_data = json.dumps(fdata, indent=2)

        return json_data

    except requests.exceptions.RequestException as e:
        return JSONResponse(content={"error": f"Request Exception: {str(e)}"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": f"An error occurred: {str(e)}"}, status_code=500)


@app.get("/scraping/")
async def scrape_train_running_status(TraiNo: str, journeyDate : str):
    Data = fetch_train_data(TraiNo, journeyDate)
    result = json.loads(Data)
    if isinstance(result, list) and len(result) == 0:
        return JSONResponse(content={"Error": "Please check Train Number or Journey Date is not correct... try again"},
                            status_code=400)
    else:
        # Return the JSON response
        return JSONResponse(result)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)


