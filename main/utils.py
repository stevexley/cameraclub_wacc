import io
import re 
import nltk
import cv2
import os
from zipfile import ZipFile
import numpy as np
from PIL import Image
from nltk.corpus import stopwords
from itertools import chain
from datetime import datetime, timedelta
from .models import Event, Competition, CompetitionType, Award, Image, Rule
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse, FileResponse
from django.contrib import messages
from django.utils.encoding import force_str
from django.utils.text import slugify
from django.conf import settings
from django.contrib.auth.decorators import permission_required

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

# def checkMono(photo, hue_threshold=2):
    # try:
    #     # Read the image
    #     img = photo2img(photo)

    #     # Convert the image to the HSV color space
    #     hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    #     # Extract the hue channel
    #     hue_channel = hsv_image[:, :, 0]

    #     # Calculate the standard deviation of the hue channel
    #     hue_std = np.std(hue_channel)

    #     # Compare the standard deviation to the hue threshold
    #     if hue_std <= hue_threshold:
    #         return True
    #     else:
    #         return False
    
def checkMono(photo, unique_colors_threshold=64):
    try:
        # Read the image
        img = photo2img(photo)

        # Convert the image to grayscale
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Calculate the number of unique colors in the image
        unique_colors = len(np.unique(gray_img))

        # Compare the number of unique colors to the threshold
        if unique_colors <= unique_colors_threshold:
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

@permission_required("main.change_event")   
def createwaccevents(request):
    '''Creates the standard Events for the following year
    Workshops on 1st Monday of each month (Jan - Nov)
    Comp Nights on 3rd Monday of each Month (Jan - Nov)
    Annual Dinner 1st Monday in December.
    Clean up will be needed but this saves a bunch of repetative creation.'''
    year = datetime.now().year + 1
    for month in range (1,12):
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

@permission_required("main.change_event")
def move_imported_events(request):
    '''In the old Access DB all the competition nights were 
    listed as the 1st of the month.  That data has been used 
    to create all the past events so the dates are wrong.'''
    # from 2011 to 2022
    #for year in range(2011,2024):
    year = 2024
    for month in range(1,12):
        old_date = (year, month, 1)
        compdate = nth_weekday(old_date, 3, 0)
        start_time = datetime.strptime("19:30", "%H:%M").time()
        end_time = datetime.strptime("21:30", "%H:%M").time()
        start_datetime = datetime.combine(compdate, start_time)
        end_datetime = datetime.combine(compdate, end_time)
        events = Event.objects.filter(starts__year = year, starts__month = month, name__icontains = "Competition")
        events.update(starts=start_datetime, ends=end_datetime)
            
    return HttpResponse("Competition Dates Fixed")

@permission_required("main.change_event")
def move_comps_to_1st(request):
    '''In the old Access DB all the competition nights were 
    listed as the 1st of the month.  To easy import of that 
    data set all events and comp dates to 1st of month.'''

    compevents = Event.objects.filter(name__icontains = "Competition")
    for event in compevents:
        year = event.starts.year
        month = event.starts.month
        starts = datetime(year, month, 1, 19, 30)
        ends = datetime(year, month, 1, 21, 30)
        events = Event.objects.filter(starts__year = year, starts__month = month, name__icontains = "Competition")
        events.update(starts=starts, ends=ends)
            
    return HttpResponse("Competition Dates Set to 1st")

def award_gold(request, comp_pk, image_pk):
    '''Award a gold judge's award to the image in the comp
    Remove any other judge's awards if they exist'''
    awards = Award.objects.filter(
        image_id = image_pk,
        type__awarded_by__awarded_by = "judge's award",
        competition_id = comp_pk
    )
    if awards:
        for award in awards:
            award.delete()
    gold = Award.objects.create(
        image_id = image_pk,
        type_id = 1,
        competition_id = comp_pk
    )
    gold.save()
    return HttpResponse("Gold Awarded")

def award_silver(request, comp_pk, image_pk):
    '''Award a silver judge's award to the image in the comp'''
    awards = Award.objects.filter(
        image_id = image_pk,
        type__awarded_by__awarded_by = "judge's award",
        competition_id = comp_pk
    )
    if awards:
        for award in awards:
            award.delete()
    silver = Award.objects.create(
        image_id = image_pk,
        type_id = 2,
        competition_id = comp_pk
    )
    silver.save()
    return HttpResponse("Silver Awarded")

def award_bronze(request, comp_pk, image_pk):
    '''Award a silver judge's award to the image in the comp'''
    awards = Award.objects.filter(
        image_id = image_pk,
        type__awarded_by__awarded_by = "judge's award",
        competition_id = comp_pk
    )
    if awards:
        for award in awards:
            award.delete()
            
    bronze = Award.objects.create(
        image_id = image_pk,
        type_id = 3,
        competition_id = comp_pk
    )
    bronze.save()
    return HttpResponse("Bronze Awarded")

def import_pics(request):
    '''Loop through images, find files in media directory that match author name and title
    add matching filename as photo.'''
    images = Image.objects.filter(photo=None)
    directory = settings.PHOTOS_ROOT
    for img in images:
        title = img.title.lower()
        name = img.author.firstname.lower() + "_" + img.author.surname.lower()
        for pic in os.listdir(directory):
            FileName = os.fsdecode(pic)
            filename = FileName.lower()
            if title in filename:
                if name in filename:
                    img.photo = "photos/" + FileName
                    img.save()
                    with open('import.log', "a") as logfile:
                        logfile.write(FileName + " added to " + str(img))
                        logfile.write("\n")
                else:
                    with open('import.log', "a") as logfile:
                        logfile.write(filename + " does not match " + str(img.author))
                        logfile.write("\n")
    return HttpResponse("Imported Pics")
                    
def cleanup_photos(request):
    '''Remove badly imported photos'''
    images = Image.objects.filter(photo = '')
    for img in images:
        img.photo = None
        img.save()

def zip_comp_images(request, comp_pk):
    comp = Competition.objects.get(id=comp_pk)
    images = Image.objects.filter(competitions=comp, photo__isnull=False).distinct()

    zip_buffer = io.BytesIO()
    zipname = f"WACC_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

    with ZipFile(zip_buffer, 'w') as myzip:
        for image in images:
            imagefile = os.path.join(settings.MEDIA_ROOT, str(image.photo))
            # Slugify for safe filenames
            newname = f"{slugify(image.author.firstname)}-{slugify(image.author.surname)}_{slugify(image.title)}.jpg"
            myzip.write(imagefile, newname)

    zip_buffer.seek(0)  # Go to the beginning of the BytesIO object

    response = FileResponse(zip_buffer, as_attachment=True, filename=zipname)
    return response

def pick_a_pic(event_pk):
    comps = Competition.objects.filter(event__id = event_pk,
                                       type__type = 'Set Digital')
    value = 0
    for comp in comps:
        images = Image.objects.filter(competitions = comp,
                                    award__type = 1)
        if not images:
            images = Image.objects.filter(competitions = comp,
                                            award__type = 4)
        for image in images:
            if image:
                value = image.id
                break
    return value

@permission_required("main.change_event")
def set_comp_images(request):
    for event in Event.objects.filter(competition__isnull = False):
        imageid = pick_a_pic(event.id)
        
    return HttpResponse(200)

@permission_required("main.change_event")
def set_comp_image(request, event_pk):
    event = Event.objects.get(id = event_pk)
    imageid = pick_a_pic(event.id)
    if imageid > 0:
        image = Image.objects.get(id = imageid)
        if image.photo:
            event.image = image
            event.save()
    return HttpResponse(200)