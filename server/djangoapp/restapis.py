import requests
import json
from .models import CarDealer, DealerReview
from django.core import serializers
from requests.auth import HTTPBasicAuth
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.environ.get("API_KEY")
# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))
def get_request(url, **kwargs):
    print(kwargs)
    print("GET from {} ".format(url))
    try:
            response = requests.get(url, headers={'Content-Type': 'application/json'},
            params=kwargs)
    except:
        #if any error
        print("Network exception occurred")
        status_code = response.status_code
        print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data

# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)
def post_request(url, json_payload, **kwargs):
    print(kwargs)
    response = requests.post(url, params=kwargs, json=json_payload)
    return response

# Create a get_dealers_from_cf method to get dealers from a cloud function
# def get_dealers_from_cf(url, **kwargs):
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list
def get_dealers_from_cf(url, **kwargs):
    results = []
    st = kwargs.get("st")
    id = kwargs.get("dealerId")
    #Call get_request with URL Param
    if st:
        json_result = get_request(url, st=st)
    elif id:
        json_result = get_request(url, dealerId=id)
    else:
        json_result = get_request(url)

    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result["dealerships"]
        for dealer in dealers:
            if st or id:
                dealer_doc = dealer
            else:
                dealer_doc = dealer["doc"]
            dealer_obj = CarDealer(
                address=dealer_doc["address"],
                city=dealer_doc["city"],
                full_name=dealer_doc["full_name"],
                id=dealer_doc["id"],
                lat=dealer_doc["lat"],
                long=dealer_doc["long"],
                short_name=dealer_doc["short_name"],
                st=dealer_doc["st"],
                zip=dealer_doc["zip"],
                state=dealer_doc["state"]
                )
            results.append(dealer_obj)
        return results

# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
# def get_dealer_by_id_from_cf(url, dealerId):
# - Call get_request() with specified arguments
# - Parse JSON results into a DealerView object list
def get_dealer_reviews_from_cf(url, **kwargs):
    results = []
    dealerId = kwargs.get("dealerId")
    json_result = get_request(url, dealerId=dealerId)

    if json_result:
        reviews = json_result["dealerReviews"]

        for review in reviews:
            sentiment = analyze_review_sentiments(review["review"])
            if review["purchase"] is False:
                review_obj = DealerReview(
                    name = review["name"],
                    purchase = review["purchase"],
                    dealership = review["dealership"],
                    review = review["review"],
                    purchase_date = None,
                    car_make = "",
                    car_model = "",
                    car_year = "",
                    sentiment = sentiment,
                    id = review["id"]
                )
                print(review_obj.sentiment)
                results.append(review_obj)
            else:
                review_obj = DealerReview(
                    name = review["name"],
                    purchase = review["purchase"],
                    dealership = review["dealership"],
                    review = review["review"],
                    purchase_date = review["purchase_date"],
                    car_make = review["car_make"],
                    car_model = review["car_model"],
                    car_year = review["car_year"],
                    sentiment = sentiment,
                    id = review["id"]
                )
                print(review_obj.sentiment)
                results.append(review_obj)
        return results

# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# def analyze_review_sentiments(text):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative
def analyze_review_sentiments(dealerreview):
    url = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/4ce35e51-408e-40b6-934f-195e479cd3ae"
    authenticator = IAMAuthenticator(api_key)
    nlu = NaturalLanguageUnderstandingV1(
        version='2021-08-01',
        authenticator=authenticator)
    nlu.set_service_url(url)

    json_result = nlu.analyze(
        text=dealerreview,
        features=Features(sentiment=SentimentOptions()),
        return_analyzed_text = True
    ).get_result()
    sentiment = json_result['sentiment']['document']['label']
    return sentiment

#Call reviews db and return count of reviewsdict
def get_reviews_count(url):
    json_result = get_request(url)
    print(json_result["numReviews"])
    return json_result["numReviews"]
