from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django import forms
from django.forms import formset_factory, BaseFormSet, BaseInlineFormSet, inlineformset_factory
from django.forms.widgets import SplitDateTimeWidget
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from .models import Image, Competition, Subject, CompetitionType, Judge, Event, Award, AwardType, Person, User, Member
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
        source_view = kwargs.pop('source_view', None)
        pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)
        if source_view ==  'enter_competition':
            author_fixed = True
        if source_view == 'add_images':
            author_fixed = False
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
            visible.field.widget.attrs['aria-describedby'] = visible.name + 'Feedback'
        self.fields['print'].widget.attrs['class'] = 'form-check-input form-check-inline'
        self.fields['print'].widget.attrs['disabled'] = True
        self.fields['photo'].widget.attrs['class'] = 'form-control form-control-lg'
        self.fields['photo'].widget.attrs['id'] = 'fileInput'
        self.fields['author'].empty_label = '-Select Author-'
        if pk:
            competition = Competition.objects.get(id=pk)
            if "print" in competition.type.type.lower():
                self.fields['print'].initial = True
        if author_fixed:
            self.fields['author'].widget = forms.HiddenInput()
        else:
            self.fields['author'].queryset = Person.objects.filter(member__current=True)
            self.fields['photo'].widget = forms.HiddenInput()
        
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

class PhotoForm(forms.ModelForm):
    
    class Meta:
        model = Image
        fields = ('photo',)



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

class JudgeAwardForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}), required=False)
    author = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}), required=False)
    award_type = forms.ModelChoiceField(queryset=AwardType.objects.filter(awarded_by__judge=True), label='Select Award', required=False)
    image_id = forms.IntegerField(widget=forms.HiddenInput())
    competition_id = forms.IntegerField(widget=forms.HiddenInput())


JudgeAwardFormSet = formset_factory(JudgeAwardForm, extra=0)

class MemberAwardForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}), required=False)
    author = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}), required=False)
    award_type = forms.ModelChoiceField(queryset=AwardType.objects.filter(awarded_by__members=True), label='Select Award', required=False)
    image_id = forms.IntegerField(widget=forms.HiddenInput())
    competition_id = forms.IntegerField(widget=forms.HiddenInput())

MemberAwardFormSet = formset_factory(MemberAwardForm, extra=0)

class UserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
            visible.field.widget.attrs['aria-describedby'] = visible.name + 'Feedback'

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class PersonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
            visible.field.widget.attrs['aria-describedby'] = visible.name + 'Feedback'
            
    class Meta:
        model = Person
        exclude = ('user','firstname', 'surname')

class MemberForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
            visible.field.widget.attrs['aria-describedby'] = visible.name + 'Feedback'

    class Meta:
        model = Member
        exclude = ('person', 'joined', 'current')

class CompetitionJudgeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
            visible.field.widget.attrs['aria-describedby'] = visible.name + 'Feedback'
    
    class Meta:
        model = Competition
        fields = [ 'judge', ]

class EndOfYearEntryForm(forms.Form):
    image_id = forms.IntegerField(widget=forms.HiddenInput())
    competition = forms.ModelChoiceField(
        queryset = Competition.objects.filter(
            type__type__contains='End of Year',  
            type__active=True
        ),
        required=False,
        label='Select End of Year Competition'                                        
    )

class ImageSelectionForm(forms.Form):
    images = forms.ModelMultipleChoiceField(
        queryset=Image.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
 
    def __init__(self, user=None, user_images=None, competition=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['images'].queryset = user_images
        self.competition = competition
        self.user = user
   
    def clean_images(self):
        images = self.cleaned_data.get('images')
        if len(images) > 3:
            raise forms.ValidationError("You can only enter up to 3 images")
        return images
    
class EoyPrintSelectionForm(forms.Form):
    images = forms.ModelMultipleChoiceField(
        queryset=Image.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
 
    def __init__(self, user=None, user_images=None, competition=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['images'].queryset = user_images
        self.competition = competition
        self.user = user