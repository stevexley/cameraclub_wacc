from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django import forms
from django.forms.widgets import SplitDateTimeWidget
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from .models import Image, Competition, Subject, CompetitionType, Judge, Event
from .utils import setTitleCase, checkWidth, checkHeight, checkOneEntry, checkMono

class EventUploadForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
            visible.field.widget.attrs['aria-describedby'] = visible.name + 'Feedback'
    
    class Meta:
        model = Event
        fields = [ 'description', 'file', ]

class ImageForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        if kwargs.pop('competition_id', None):
            self.competition_id = kwargs.pop('competition_id', None)
        if kwargs.pop('gallery_id', None):
            self.gallery_id = kwargs.pop('gallery_id', None)
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
            visible.field.widget.attrs['aria-describedby'] = visible.name + 'Feedback'
        self.fields['print'].widget.attrs['class'] = 'form-check-input form-check-inline'
        competition = kwargs['initial']['competition']
        if "print" in competition.type.type.lower():
            self.fields['print'].initial = True
        self.fields['author'].widget = forms.HiddenInput()
        
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title:
            title = setTitleCase(title)
        return title
    
    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        author = self.cleaned_data.get('author')
        try:
            competition = self.initial['competition']
            if photo:
                for rule in competition.type.rules.all():
                    print(rule.rule)
                    if '<= 1920px wide' in rule.rule:
                        if checkWidth(photo):
                            pass
                        else:
                            raise ValidationError("Image is more than 1920 pixels wide")
                    if '<= 1200px high' in rule.rule:
                        if checkHeight(photo):
                            pass
                        else:
                            raise ValidationError("Image is more than 1200 pixels high")
                    if 'One Entry' in rule.rule:
                        if checkOneEntry(author, competition):
                            pass
                        else:
                            raise ValidationError("You have already uploaded an image to this competition")
                    if 'Mono' in rule.rule:
                        if checkMono(photo):
                            pass
                        else:
                            raise ValidationError("This isn't a monochrome image")
                    elif 'Colour' in rule.rule:
                        if checkMono(photo):
                            raise ValidationError("This isn't a colour image")
                        else:
                            pass
        except Exception as e:
            print(f"Error: {e}")
        return photo      
    
    class Meta:
        model = Image
        fields = ['title', 'author', 'photo', 'print']  # List the fields you want to display in the form
        
class CompForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        self.event_id = kwargs.pop('event_id', None)
        super(CompForm, self).__init__(*args, **kwargs)
        # Set default dates
        tz = ZoneInfo('Australia/Perth')
        event = Event.objects.get(id=self.event_id)
        # for visible in self.visible_fields():
        #     visible.field.widget.attrs['class'] = 'form-control'
        #     visible.field.widget.attrs['placeholder'] = visible.field.label
        #     visible.field.widget.attrs['aria-describedby'] = visible.name + 'Feedback'
        self.fields['judge_awards'].widget.attrs['class'] = 'form-check-input form-check-inline'
        self.fields['members_vote'].widget.attrs['class'] = 'form-check-input form-check-inline'
        self.fields['display_all'].widget.attrs['class'] = 'form-check-input form-check-inline'
        self.fields['display_awarded'].widget.attrs['class'] = 'form-check-input form-check-inline'
        self.fields['open_for_entries'].initial = datetime(int(event.starts.year), 1, 1, 6, 0, 0, tzinfo=tz)
        self.fields['entries_close'].initial = event.starts - timedelta(8)
        self.fields['open_for_judging'].initial = event.starts - timedelta(6)
        self.fields['judging_closes'].initial = event.starts - timedelta(6)
        # Restrict subjects to ones for this year + open
        current_year = datetime.now().year
        self.fields['subject'].queryset = Subject.objects.filter(year=current_year)
        self.fields['subject'].queryset |= Subject.objects.filter(subject='Open')
        # Set initial value to open as that's the most common one
        self.fields['subject'].initial = Subject.objects.get(subject='Open')
        self.fields['type'].queryset = CompetitionType.objects.filter(active = True)
        self.fields['judge'].queryset = Judge.objects.filter(current = True)
        # Hide event input as it's already set
        self.fields['event'].widget = forms.HiddenInput()
               
        try:
            if self.event_id is not None:
                self.fields['event'].initial = Event.objects.get(id=self.event_id)
        except ObjectDoesNotExist:
            print("Event matching query does not exist.")
        
    class Meta:
        model = Competition
        exclude = ['images',]        
        
class CompetitionNightSetupForm(forms.Form):
 
    COLOUR_CHOICES = [('colour', 'Colour'), ('mono', 'Monochrome')]

    colour_or_mono = forms.ChoiceField(choices=COLOUR_CHOICES)
    if datetime.now().month > 8:
        set_subject = forms.ModelMultipleChoiceField(queryset=Subject.objects.filter(year=datetime.now().year + 1))
    else:
        set_subject = forms.ModelMultipleChoiceField(queryset=Subject.objects.filter(year=datetime.now().year))
    # competition_types = CompetitionType.objects.all()  # Assuming you want all competition types
    