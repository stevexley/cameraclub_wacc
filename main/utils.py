import io
import re 
import nltk
import cv2
import numpy as np
from PIL import Image
from nltk.corpus import stopwords
from itertools import chain
from datetime import datetime, timedelta
from .models import Event, Competition, Award
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse
from django.contrib import messages

def setTitleCase(title):
    '''This function converts a string into titlecase while ignoring "stopwords"
    (things like and, the, in, on) to create a properly capitalised title.'''
    exceptions = []
    exceptions.append([word for word in stopwords.words('english')])
    exceptions = list(chain.from_iterable(exceptions))
    list_of_words = re.split(' ', title) 
    final = [list_of_words[0].capitalize()] 
    for word in list_of_words[1:]: 
        word = word.lower()
        if word in exceptions:
            final.append(word)
        else:
            final.append(word.capitalize())
    return " ".join(final)

def photo2img(photo):
    # Check if the uploaded file is in-memory (InMemoryUploadedFile)
    if isinstance(photo, InMemoryUploadedFile):
        # Read the in-memory file and convert it to a format OpenCV can handle
        image_data = photo.read()
        photo.seek(0)
        image = Image.open(io.BytesIO(image_data))

        # Convert the PIL image to an OpenCV image (numpy array)
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    else:
        # Handle the case where 'photo' is a file stored on disk (has a 'path' attribute)
        img = cv2.imread(photo.path)
    return img
        
def checkWidth(photo):
    '''Checks that the width of the photo is 1920 pixels or less'''
    img = photo2img(photo)
    hgt, wid, chan = img.shape
    if wid <= 1920:
        return True
    else:
        return False
    
def checkHeight(photo):
    '''Checks that the height of the photo is 1200 pixels or less'''
    img = photo2img(photo)
    hgt, wid, chan = img.shape
    if hgt <= 1200:
        return True
    else:
        return False
    
def checkOneEntry(author, competition):
    """Checks through the images in the comp and returns False
    if it finds one with the same author as the current user.
    Otherwise returns True"""
    for entry in competition.images.all():
        if entry.author == author:
            return False
    return True

def checkMono(photo, hue_threshold=10):
    try:
        # Read the image
        img = photo2img(photo)

        # Convert the image to the HSV color space
        hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Extract the hue channel
        hue_channel = hsv_image[:, :, 0]

        # Calculate the standard deviation of the hue channel
        hue_std = np.std(hue_channel)

        # Compare the standard deviation to the hue threshold
        if hue_std <= hue_threshold:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# week_day is 0-6, 0=Monday
def nth_weekday(temp, nth_week, week_day):
    temp = datetime(*temp)
    adj = (week_day - temp.weekday()) % 7
    temp += timedelta(days=adj)
    temp += timedelta(weeks=nth_week-1)
    return temp
    
def createwaccevents(request):
    '''Creates the standard Events for the following year
    Workshops on 1st Monday of each month (Jan - Nov)
    Comp Nights on 3rd Monday of each Month (Jan - Nov)
    Annual Dinner 1st Monday in December.
    Clean up will be needed but this saves a bunch of repetative creation.'''
    year = datetime.now().year + 1
    for month in range (1,11):
        first_date = (year, month, 1)
        wkshop_date = nth_weekday(first_date, 1, 0)
        start_time = datetime.strptime("19:30", "%H:%M").time()
        end_time = datetime.strptime("21:30", "%H:%M").time()
        start_datetime = datetime.combine(wkshop_date, start_time)
        end_datetime = datetime.combine(wkshop_date, end_time)

        workshop = Event.objects.create(
            name = wkshop_date.strftime("%B") + " Workshop Night",
            starts = start_datetime,
            ends =  end_datetime
            )
        workshop.save()

        compdate = nth_weekday(first_date, 3, 0)
        start_datetime = datetime.combine(compdate, start_time)
        end_datetime = datetime.combine(compdate, end_time)

        compnight = Event.objects.create(
            name = compdate.strftime("%B") + " Competition Night",
            starts = start_datetime,
            ends =  end_datetime
            )
        compnight.save()

    month = 12

    first_date = (year, month, 1)
    compdate = nth_weekday(first_date, 1, 0)
    start_time = datetime.strptime("19:30", "%H:%M").time()
    end_time = datetime.strptime("21:30", "%H:%M").time()
    
    compnight = Event.objects.create(
            name = "Awards Dinner",
            starts = datetime.combine(compdate, start_time),
            ends = datetime.combine(compdate, end_time),
        )
    compnight.save()

    return HttpResponse("Events created successfully")

def move_imported_events(request):
    '''In the old Access DB all the competition nights were 
    listed as the 1st of the month.  That data has been used 
    to create all the past events so the dates are wrong.'''
    # from 2011 to 2022
    for year in range(2011,2023):
        for month in range(1,12):
            old_date = (year, month, 1)
            compdate = nth_weekday(old_date, 3, 0)
            start_time = datetime.strptime("19:30", "%H:%M").time()
            end_time = datetime.strptime("21:30", "%H:%M").time()
            start_datetime = datetime.combine(compdate, start_time)
            end_datetime = datetime.combine(compdate, end_time)
            events = Event.objects.filter(starts__year = year, starts__month = month)
            events.update(starts=start_datetime, ends=end_datetime)
            
    return HttpResponse("Competition Dates Fixed")

def move_comps_to_1st(request):
    '''In the old Access DB all the competition nights were 
    listed as the 1st of the month.  To easy import of that 
    data set all events and comp dates to 1st of month.'''

    comps = Competition.objects.all()
    for comp in comps:
        compevent = comp.event
        daynum = compevent.starts.day - 1
        firstdate = compevent.starts + timedelta(days=(-1 * daynum))
        compevent.starts = firstdate
        compevent.ends = firstdate
        compevent.save()
            
    return HttpResponse("Competition Dates Set to 1st")

def award_gold(request, comp_pk, image_pk):
    '''Award a gold judge's award to the image in the comp'''
    gold = Award.objects.create(
        image_id = image_pk,
        type_id = 1,
        competition_id = comp_pk
    )
    gold.save()
    return HttpResponse("Gold Awarded")

def award_silver(request, comp_pk, image_pk):
    '''Award a silver judge's award to the image in the comp'''
    silver = Award.objects.create(
        image_id = image_pk,
        type_id = 2,
        competition_id = comp_pk
    )
    silver.save()
    return HttpResponse("Silver Awarded")

def award_bronze(request, comp_pk, image_pk):
    '''Award a silver judge's award to the image in the comp'''
    bronze = Award.objects.create(
        image_id = image_pk,
        type_id = 3,
        competition_id = comp_pk
    )
    bronze.save()
    return HttpResponse("Bronze Awarded")