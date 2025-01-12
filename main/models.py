import os
from datetime import datetime 
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.core.files.storage import default_storage
from django.conf import settings
from tinymce.models import HTMLField
from django.db.models import ImageField
from django.dispatch import receiver
from pdf2image import convert_from_path
from PIL import Image

# Create your models here.

class Blurb(models.Model):
    '''TextFields to be displayed on information pages on the website'''
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    contents = HTMLField()
    
    def __str__(self):
        return self.name

def generate_thumbnail(pdf_path, thumb_path, size=(200, 300)):
    # Convert the first page of the PDF file to an image
    images = convert_from_path(pdf_path)
    if images:
        first_page_image = images[0]
        # Resize the image
        resized_image = first_page_image.resize(size)
        # Save the resized image as a thumbnail
        resized_image.save(thumb_path, 'PNG')

class Newsletter(models.Model):
    '''Club Newsletters (issued monthly)'''
    id = models.AutoField(primary_key=True)
    issue_date = models.DateTimeField(default=datetime.now())
    file = models.FileField(upload_to='files/news/')
    thumb = models.ImageField(upload_to='files/news/thum', blank=True, null=True)
    
    def __str__(self):
        return "Newsletter: " + self.issue_date.strftime("%d/%m/%Y")

@receiver(models.signals.post_save, sender=Newsletter)
def make_thumbnail(sender, instance, **kwargs):
    if instance.thumb:
        return
    if instance.file:
        pdf_path = instance.file.path
        thumb_path = os.path.join(os.path.dirname(pdf_path), 'thumbnails', f"{instance.id}.png")
        generate_thumbnail(pdf_path, thumb_path)
        instance.thumb = os.path.relpath(thumb_path, settings.MEDIA_ROOT)
        instance.save(update_fields=['thumb'])

class Person(models.Model):
    '''The person model that contains contact details for a person.
    A Person can be a Member or a Judge (or neither).
    A Person can be a User or not.'''
    id = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    mobile = models.CharField(max_length=50, null=True, blank=True)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.PROTECT)
    
    def __str__(self):
        return self.firstname + " " + self.surname
    
    def listname(self):
        return self.surname + ', ' + self.firstname
    
    class Meta:
        ordering = ["surname", "firstname"]
    
class Member(models.Model):
    '''The member model that contains present and past members.
    Images belong to Members.'''
    id = models.AutoField(primary_key=True)
    person = models.OneToOneField(Person, on_delete=models.CASCADE)
    joined = models.DateField(null=True, blank=True)
    current = models.BooleanField(default=True)
    
    def __str__(self):
        return self.person.firstname + " " + self.person.surname
    
    class Meta:
        ordering = ["person__firstname"]
    
class Payment(models.Model):
    '''money paid by a member, for use by the Treasurer'''
    id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    paid_for = models.CharField(max_length=150) 

class Position(models.Model):
    '''Positions on the Committee, used to create Contacts list'''
    id = models.AutoField(primary_key=True)
    position = models.CharField(max_length=50)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='position')
    order = models.SmallIntegerField()
    
    def __str__(self):
        return self.position
    
    class Meta:
        ordering = ["order"]
    
class Judge(models.Model):
    '''The Judge model that contains present and past judges.'''
    id = models.AutoField(primary_key=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='judge')
    current = models.BooleanField(default=True)
    notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.person.firstname + " " + self.person.surname
    
class Image(models.Model):
    '''Images entered into competitions or uploaded to galleries,
    may have no image file if it was a print competition entry with no subsequent upload.'''
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Person, on_delete=models.PROTECT)
    print = models.BooleanField(default=False, verbose_name="Entered as a print")
    photo = models.ImageField(upload_to='photos/', null=True, blank=True)
    
    def __str__(self):
        return self.title + ": " + self.author.firstname + " " + self.author.surname

    class Meta:
        ordering = ["title", "author", "print"]

def file_cleanup(sender, **kwargs):
    """
    Remove the jpg when removing an Image object from the database
    Prevents buildup of orphaned images

    Copied from https://timonweb.com/django/cleanup-files-and-images-on-model-delete-in-django/
    just changed to assign 'photo' as the field name
    As not all Image instances have a file I had to add the try before if( hasattr...
    """
    
    fieldname = 'photo'
    try:
        field = sender._meta.get_field(fieldname)
    except:
        field = None

    if field and isinstance(field, ImageField):
        inst = kwargs["instance"]
        f = getattr(inst, fieldname)
        m = inst.__class__._default_manager
        try:
            if (
                hasattr(f, "path")
                and os.path.exists(f.path)
                and not m.filter(
                    **{"%s__exact" % fieldname: getattr(inst, fieldname)}
                ).exclude(pk=inst._get_pk_val())
            ):
                try:
                    default_storage.delete(f.path)
                except:
                    pass
        except:
            pass
   
post_delete.connect(
    file_cleanup, sender=Image, dispatch_uid="gallery.image.file_cleanup"
)

class Event(models.Model):
    '''An Event is anything with a start and end datetime and can include galleries and/or competitions.
    The most common Events are competition nights which will have a number of competitions, workshops and outings,
    these may have non-competition galleries.'''
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    starts = models.DateTimeField()
    ends = models.DateTimeField()
    file = models.FileField(upload_to='files/', null=True, blank=True)
    image = models.ForeignKey(Image, null=True, blank=True, on_delete=models.CASCADE)
    
    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension
    
    def __str__(self):
        return self.name + " (" + self.starts.strftime("%m/%d/%Y") + ")"
    
    class Meta:
        ordering = ['starts']

class Rule(models.Model):
    '''A Rule is a restriction on a Competition'''
    id = models.AutoField(primary_key=True)
    rule = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.rule
    
    class Meta:
        ordering = ['description']

class CompetitionType(models.Model):
    '''A Competition is a collection of images for a club Competition'''
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=50)
    rules = models.ManyToManyField(Rule, blank=True)
    active = models.BooleanField(default=True)
    contributes_to_annual = models.BooleanField(default=True)
    selection_not_places = models.BooleanField(default=False)
    
    def __str__(self):
        return self.type

class Subject(models.Model):
    '''A Subject is the description of the images that may be entered into a Competition.
    There may be mutiple Competitions with the same subject.  For example lots of Open Colour 
    and Open Mono Subject Competitions and Digital and Print Competitions with the same Subject'''
    id = models.AutoField(primary_key=True)
    subject = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    year = models.SmallIntegerField(null=True)
    
    def __str__(self):
        return self.subject
   
class Competition(models.Model):
    '''A Competition is a collection of images for a club competition and is held at an Event'''
    id = models.AutoField(primary_key=True)
    subject = models.ForeignKey(Subject, null=True, on_delete=models.PROTECT)
    open_for_entries = models.DateTimeField(null=True)
    entries_close = models.DateTimeField(null=True)
    open_for_judging = models.DateTimeField(null=True)
    judging_closes =  models.DateTimeField(null=True)
    judge_awards = models.BooleanField(default=True)
    members_vote = models.BooleanField(default=True)
    judge = models.ForeignKey(Judge, null=True, blank=True, on_delete=models.PROTECT)
    type = models.ForeignKey(CompetitionType, on_delete=models.PROTECT)
    images = models.ManyToManyField(Image, related_name='competitions', blank=True)
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    display_all = models.BooleanField(default=False)
    display_awarded = models.BooleanField(default=True)
    
    def __str__(self):
        if self.subject.subject == 'Open Colour' or self.subject.subject == 'Open Mono':
            return str(self.event.starts.year) + " " + self.event.name + ": " + self.type.type 
        else:
            return str(self.event.starts.year) + " " + self.event.name + ": " + self.type.type + " (" + self.subject.subject + ")"

    class Meta:
        ordering = ["-event__starts"]
        
class Awarder(models.Model):
    id = models.AutoField(primary_key=True)
    awarded_by = models.CharField(max_length=100, blank=True)
    judge = models.BooleanField(default=False)
    members = models.BooleanField(default=True)
    
    def __str__(self):
        return self.awarded_by
    
class AwardType(models.Model):
    '''A list of all the awards and what they are worth in terms of points
    If the points change create a new award and make the old one not active.
    This means that old scores will stay the same.'''
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    awarded_by = models.ForeignKey(Awarder, on_delete=models.PROTECT)
    points = models.SmallIntegerField(default=0)
    display_award = models.BooleanField(default=True)
    display_image = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ["-points"]

class Award(models.Model):
    '''Awards to an Image'''
    id = models.AutoField(primary_key=True)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    type = models.ForeignKey(AwardType, on_delete=models.PROTECT)
    competition = models.ForeignKey(Competition, null=True, on_delete=models.PROTECT)  # null for awards outside club comps
    
    def __str__(self):
        return self.image.author.firstname + " " + self.image.author.surname + " was awarded a " + self.type.name + " " + self.type.awarded_by.awarded_by + " for '" +  self.image.title + "'"

class Gallery(models.Model):
    '''A Gallery is a collection of images which isn't a club competition'''
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    images = models.ManyToManyField(Image, related_name='galleries')
    event = models.ForeignKey(Event, null=True, on_delete=models.PROTECT)
    public_after = models.DateTimeField(null=True)
    member_upload_from = models.DateTimeField(null=True)
    member_upload_until = models.DateTimeField(null=True)
    
    def __str__(self):
        return self.name
    
class ImageCompetitionComment(models.Model):
    '''Judges can type in comments while reviewing images to read out on comp night'''
    id = models.AutoField(primary_key=True)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    comment = models.TextField(null=True)
    
class VoteOption(models.Model):
    '''Types of Vote that can be made (in WACCs case 1st 2nd 3rd)'''
    id = models.AutoField(primary_key=True)
    option = models.CharField(10)
    points = models.SmallIntegerField(default=0)
    active = models.BooleanField(default=True)
    judge_only = models.BooleanField(default=False)
    # exclusive means one vote of this type per member per competition 
    exclusive = models.BooleanField(default=True)
    
    def __str__(self):
        return self.option
    
class Vote(models.Model):
    '''A vote by a Member for an Image in a Competition'''
    id = models.AutoField(primary_key=True)
    vote = models.ForeignKey(VoteOption, on_delete=models.PROTECT)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    voter = models.ForeignKey(Member, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.competition.event.name + ": " + self.competition.type.type + " (" + self.competition.subject.subject + ")" + ": " + self.vote.option + " to " + self.image.title + ": " + self.image.author.firstname + " " + self.image.author.surname + " from " + self.voter.person.firstname + " " + self.voter.person.surname