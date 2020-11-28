import requests
import json
import os
from dotenv import load_dotenv
from datetime import date

# load env vars
load_dotenv()

# save env vars as constants
SHEET_BASE_API = os.getenv("SHEET_BASE_API")
FLIGHT_API_KEY = os.getenv("FLIGHT_API_KEY")
FLIGHT_BASE_API = os.getenv("FLIGHT_BASE_API")
FLIGHT_DESTINATION_API = os.getenv("FLIGHT_DESTINATION_API")
FLIGHT_QUOTES_API = os.getenv("FLIGHT_QUOTES_API")
FLIGHT_DEPARTURE_DATE = os.getenv("FLIGHT_DEPARTURE_DATE")
FLIGHT_RETURN_DATE = os.getenv("FLIGHT_RETURN_DATE")

######################################################################

# load sheet data
response = requests.get(SHEET_BASE_API)

rows_data = response.text

row_list = json.loads(rows_data)["sheet1"]

# extract all the destinations from sheet
destinations = [row["city"] for row in row_list]

FLIGHT_GET_DESTINATION_API = f"https://{FLIGHT_BASE_API}/{FLIGHT_DESTINATION_API}"

FLIGHT_API_HEADERS = {
    'x-rapidapi-key': FLIGHT_API_KEY,
    'x-rapidapi-host': FLIGHT_BASE_API
}

airport_codes = []

for destination in destinations:
    querystring = {"query": destination}

    # get airport details for each city
    response = requests.get(FLIGHT_GET_DESTINATION_API, headers=FLIGHT_API_HEADERS, params=querystring)

    # extract and store airport code for each city in a list
    query_result = response.text
    query_result_dict = json.loads(query_result)
    aiport_id = query_result_dict["Places"][0]["PlaceId"]
    airport_codes.append(aiport_id)

######################################################################

# first entry in sheet starts from row number 2
row_number = 2

for code in airport_codes:

    FLIGHT_GET_QUOTES_API = f"https://{FLIGHT_BASE_API}/{FLIGHT_QUOTES_API}/{code}/{FLIGHT_DEPARTURE_DATE}"

    querystring = {"inboundpartialdate": FLIGHT_RETURN_DATE}

    # get carrier and pricing for each destination using airport code
    response = requests.get(FLIGHT_GET_QUOTES_API, headers=FLIGHT_API_HEADERS, params=querystring)

    quotes_json = json.loads(response.text)
    quotes = quotes_json["Quotes"]

    min_price = 0

    # from multiple quotes available, get the minimum price
    for quote in quotes:
        if min_price == 0:
            min_price = quote['MinPrice']
        elif min_price > quote['MinPrice']:
            min_price = quote['MinPrice']

    # store single row from sheet, identified by value of row number in loop
    match_row = [row for row in row_list if row['id'] == row_number][0]

    # update the sheet only if one of following conditions are true -
    # price was missing OR old price is greater than the current minimum price
    if "price" not in match_row or match_row["price"] > min_price:
        SHEET_PUT_API = f"{SHEET_BASE_API}/{row_number}"

        sheet_input = {
            "sheet1": {
                "airportCode": code,
                "price": min_price
            }
        }
        
        response = requests.put(SHEET_PUT_API, json=sheet_input)

    # increment row counter to loop through all the rows of sheet
    row_number += 1

######################################################################