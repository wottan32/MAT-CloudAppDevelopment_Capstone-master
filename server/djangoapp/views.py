from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarDealer, CarModel
from .restapis import (get_request, get_dealers_from_cf, get_dealer_reviews_from_cf, post_request,
                    get_reviews_count)
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime, date
import logging
import json
import pdb

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    if request.method == "GET":
        return render(request, 'djangoapp/about.html')


# Create a `contact` view to return a static contact page
def contact(request):
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html')

# Create a `login_request` view to handle sign in request
def login_request(request):
    if request.method == "POST":
        username = request.POST['uname']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
    if user is not None:
        login(request,user)
        return redirect('djangoapp:index')
    else:
        return render(request, 'djangoapp/registration.html')

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    if request.method == "GET":
        return render(request, 'djangoapp/registration.html')
    elif request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exists = False
        try:
            User.objects.get(username=username)
            user_exists = True
        except:
            print('{} user name is taken'.format(username))

    if not user_exists:
        user = User.objects.create_user(username=username, first_name=first_name,
            last_name=last_name, password=password)
        login(request, user)

        return redirect('djangoapp:index')
    else:
        return render(request, 'djangoapp/registration.html')


# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    if request.method == "GET":
        url = "https://d47998ca.us-south.apigw.appdomain.cloud/api/api/dealership"
        dealerships = get_dealers_from_cf(url)
        dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        context = {'dealerships' : dealerships}
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
# ...
def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == "GET":
        url = "https://d47998ca.us-south.apigw.appdomain.cloud/api/review"
        dealer_details = get_dealer_reviews_from_cf(url, dealerId=dealer_id)
        #reviews = '\n'.join(review.review+" "+review.sentiment for review in dealer_details)
        reviewsdict = (vars(review) for review in dealer_details)
        context = {"Reviews":reviewsdict, "dealerId":dealer_id}
        print(reviewsdict)
    return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
def add_review(request, dealer_id):

    if request.user.is_authenticated:
        context={}
        if request.method == "GET":
            cars = CarModel.objects.filter(dealer_id=dealer_id)
            context['cars'] = cars
            context['dealer_id']=dealer_id
            return render(request, 'djangoapp/add_review.html', context)
        elif request.method == "POST":
            print(request.POST)
            url = "https://d47998ca.us-south.apigw.appdomain.cloud/api/review"
            review = {}
            review["id"] = get_reviews_count(url) + 1
            review["time"] = datetime.utcnow().isoformat()
            review["dealerId"] = dealer_id
            review["review"] = request.POST["content"]
            review["name"] = request.user.username
            if request.POST['purchasecheck'] == "on":
                review["purchase"] = True
            else:
                review["purchase"] = False
            review["purchase_date"]= request.POST["purchasedate"]
            review["car_make"]= "Jeep"
            review["car_model"]= "Gladiator"
            review["car_year"]= 2021

            json_payload = {}
            json_payload = review
            response = post_request(url, json_payload, params=review)
            return redirect('djangoapp:dealer_details', dealer_id=dealer_id)
        else:
            return HttpResponse("Invalid Request type: " + request.method)
    else:
        return HttpResponse("User not authenticated")
