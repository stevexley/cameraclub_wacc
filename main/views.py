from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.dates import YearArchiveView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin
from django.views.generic import CreateView, UpdateView, TemplateView, FormView
from django.forms import inlineformset_factory
from django.db.models import Sum, Max, Min

from .models import Image, Event, Competition, CompetitionType, Person, Member, User, Blurb, \
    Gallery, VoteOption, Vote, Award, AwardType, Subject, Position, Newsletter
from .forms import *
from datetime import datetime, timedelta
import subprocess

class ProfileView(LoginRequiredMixin, DetailView):
    login_url = "accounts/login/"
    redirect_field_name = "redirect_to"
    model = Member
    template_name = 'main/member_profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = context['member'].person
        
        images = {}
        
        #Get oldest image
        oldest_entry = Image.objects.filter(author=person).aggregate(Min('competitions__entries_close'))
        oldest_entry_date = oldest_entry['competitions__entries_close__min']
        if oldest_entry_date:
            firstyear =  oldest_entry_date.year
        
        for year in range(datetime.now().year, (firstyear - 1), -1):
            entries = {
                'year': year,
                'images': Image.objects.filter(author = person,
                                                competitions__judging_closes__year = year
                                                ).order_by('competitions__judging_closes')
            }
            images[year] = entries
            context['images'] = images
        return context
    
    
class MemberListView(PermissionRequiredMixin, ListView):
    model = Member
    permission_required = "main.change_member"
    template_name = 'main/membership_list.html'
    context_object_name = 'members'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['committee'] =  User.objects.filter(groups__name='Committee').order_by('person__position__order')     
        return context
    

class MainGalleryView(ListView):
    '''This is the main display of images on the front page
    It displays upto 200 most recent images with an award with
    display_award = True.  Some awards have display_award = False 
    this allows for Entrance awards that give points but aren't 
    given by members' votes or judge's choices.'''
    model = Image
    template_name = 'main/maingallery.html'
    context_object_name = 'images'
    
    #annotate needed to prevent image duplicates
    #exclude image objects with no image file
    def get_queryset(self):
        images = Image.objects.filter(photo__icontains = 'photo',
            award__type__display_award=True
        ).annotate(max_end=Max('award__competition__judging_closes')).order_by("-max_end")[:200]
        
        return images

class AboutUsView(View):
    '''This view just selects the Blub object that contains
    the HTML of the About Us page.  This allows for easy 
    editing of the page from the admin pages without having
    to touch the code.'''
    template_name = 'main/about_us.html'
    
    def get(self, request):
        blurb = Blurb.objects.filter(name="About Us").first()
        if blurb:
            return render(request, self.template_name, {'object': blurb})
        else:
            # Handle the case when the object is not found (e.g., return an error page)
            return render(request, 'main/error.html')
 
class NewslettersView(YearArchiveView):
    '''This page shows the club newsletters by year'''
    model = Newsletter
    date_field = 'issue_date'
    make_object_list = True
    context_object_name = 'newsletters'
    template_name = 'main/news.html'
    
    def get_year(self):
        """Return the year for which this view should display data.
        year can be set in the url, if not set it defaults to this year"""
        year = self.year
        if year is None:
            try:
                year = self.kwargs["year"]
            except:
                year = datetime.now().year
        return year
    
    def get_queryset(self):
        year = self.get_year()
        return Newsletter.objects.filter(issue_date__year=year).order_by('issue_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.get_year()
        context['next_year'] = None
        context['previous_year'] = None
        if Newsletter.objects.filter(issue_date__year=(year - 1)):
            context['previous_year'] = year - 1
        if Newsletter.objects.filter(issue_date__year=(year + 1)):
            context['next_year'] = year + 1
        return context

class EventsView(YearArchiveView):
    '''This page lists all open events with the competitions
    and galleries in them by year.'''
    model = Event
    date_field = 'starts'
    make_object_list = True
    allow_future = True
    context_object_name = 'events'
    template_name = 'main/events.html'
    
    def get_year(self):
        """Return the year for which this view should display data.
        year can be set in the url, if not set it defaults to this year"""
        year = self.year
        if year is None:
            try:
                year = self.kwargs["year"]
            except:
                year = datetime.now().year
        return year
    
    def get_queryset(self):
        year = self.get_year()
        return Event.objects.filter(starts__year=year).prefetch_related('competition_set', 'gallery_set')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.get_year()
        context['next_year'] = None
        context['previous_year'] = None
        if Event.objects.filter(starts__year=(year - 1)):
            context['previous_year'] = year - 1
        if Event.objects.filter(starts__year=(year + 1)):
            context['next_year'] = year + 1
        return context

@permission_required("main.change_event")
def generate_pdf_thumbnail(pdf_path, thumbnail_path):
    '''Convert the first page of the PDF to a PNG image using pdftoppm
    Need to add a trigger when pdf is uploaded to perform this function'''
    cmd = [
        "pdf2image",
        "-png",         # Output format (you can choose PNG or JPEG)
        "-f", "1",      # First page
        "-l", "1",      # Last page (first page in this case)
        pdf_path,
        thumbnail_path  # Output image path
    ]
    subprocess.run(cmd)

    # Usage
    # pdf_path = "path/to/your.pdf"
    #thumbnail_path = "path/to/your/thumbnail.png"

    # generate_pdf_thumbnail(pdf_path, thumbnail_path)

class EventDetailView(DetailView):
    model = Event
    template_name = 'main/event_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comps'] = Competition.objects.filter(event = context['object'])
        context['user'] = self.request.user
        return context
    
class UploadEventFileView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    """This is the view for uploading a file to an event.
    """
    permission_required = "main.change_event"
    model = Event  
    form_class = EventUploadForm
    template_name = 'main/event_upload_form.html'
    success_url = '/events/' + str(datetime.now().year) + '#today_bookmark'
    success_message = "Event Updated"

class CompCreateView(PermissionRequiredMixin, CreateView):
    model = Competition
    permission_required = "main.change_competition"
    form_class = CompForm
    template_name = 'main/comp_form.html'
    
    def get_form_kwargs(self):
        kwargs = super(CompCreateView, self).get_form_kwargs()
        kwargs.update({'event_id': self.kwargs['event_id']})  # to pass event id to form
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = Event.objects.get(id=self.kwargs['event_id'])
        return context
    
    def get_success_url(self):
        # Redirect to the EventDetailView for the event associated with the competition
        return reverse_lazy('event', kwargs={'pk': self.kwargs['event_id']})

@permission_required("main.change_competition")
def setup_competition_night(request, event_id):
    '''Creat the standard set of competitions for a competition night
    Colour or Mono Open for prints & digital plus set for prints and digital
    Event id provided in url, subject and mono/colour in form'''

    event = Event.objects.get(pk=event_id)

    if request.method == 'POST':
        form = CompetitionNightSetupForm(request.POST)
        if form.is_valid():
            colour_or_mono = form.cleaned_data['colour_or_mono']
            set_subject = form.cleaned_data['set_subject']

            if colour_or_mono == 'colour':
                opencolourprint = CompetitionType.objects.get(active=True,
                                                         type = 'Colour Open Print')
                competition1 = Competition.objects.create(
                        subject=Subject.objects.get(subject="Open"),
                        open_for_entries=event.starts - timedelta(days = 90),
                        entries_close=event.starts - timedelta(days = 8),
                        judging_closes=event.ends - timedelta(hours = 1),
                        type=opencolourprint,
                        event=event
                )
                competition1.save()
                
                opencolourdigital = CompetitionType.objects.get(active=True,
                                                         type = 'Colour Open Digital')
                competition2 = Competition.objects.create(
                        subject=Subject.objects.get(subject="Open"),
                        open_for_entries=event.starts - timedelta(days = 90),
                        entries_close=event.starts - timedelta(days = 8),
                        judging_closes=event.ends - timedelta(days = 2),
                        type=opencolourdigital,
                        event=event
                )
                competition2.save()
            else:
                openmonoprint = CompetitionType.objects.get(active=True,
                                                         type = 'Mono Open Print')
                competition1 = Competition.objects.create(
                        subject=Subject.objects.get(subject="Open"),
                        open_for_entries=event.starts - timedelta(days = 90),
                        entries_close=event.starts - timedelta(days = 8),
                        judging_closes=event.ends - timedelta(hours = 1),
                        type=openmonoprint,
                        event=event
                )
                competition1.save()
                
                openmonodigital = CompetitionType.objects.get(active=True,
                                                         type = 'Mono Open Digital')
                competition2 = Competition.objects.create(
                        subject=Subject.objects.get(subject="Open"),
                        open_for_entries=event.starts - timedelta(days = 90),
                        entries_close=event.starts - timedelta(days = 8),
                        judging_closes=event.ends - timedelta(days = 2),
                        type=openmonodigital,
                        event=event
                )
                competition2.save()
                
            setprint = CompetitionType.objects.get(active=True,
                                                         type = 'Set Print')
            competition3 = Competition.objects.create(
                    subject=set_subject[0],
                    open_for_entries=event.starts - timedelta(days = 90),
                    entries_close=event.starts - timedelta(days = 8),
                    judging_closes=event.ends - timedelta(hours = 1),
                    type=setprint,
                    event=event
            )
            competition3.save()
            
            setdigital = CompetitionType.objects.get(active=True,
                                                        type = 'Set Digital')
            competition4 = Competition.objects.create(
                    subject=set_subject[0],
                    open_for_entries=event.starts - timedelta(days = 90),
                    entries_close=event.starts - timedelta(days = 8),
                    judging_closes=event.ends - timedelta(days = 2),
                    type=setdigital,
                    event=event
            )
            competition4.save()        
                        
            return redirect('event', event_id)  # Redirect to event detail page
    else:
        form = CompetitionNightSetupForm()

    return render(request, 'main/setup_competition_night.html', {'form': form, 'event': event})
      
class EnterCompetitionView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """This is the view for submitting a photo to a competition.
    It creates an Image object, if there is a photo uploaded the photo is validated 
    against the competition rules, where possible, the validation (and capitalisation
    of the title) happen in the ImageForm."""
    login_url = "accounts/login/"
    redirect_field_name = "redirect_to"
    model = Image  
    form_class = ImageForm
    template_name = 'main/image_upload_form.html'
    success_url = '/events/' + str(datetime.now().year) + '/#today_bookmark'
    success_message = "Entry Uploaded"

    def get_initial(self):
        competition = Competition.objects.get(id=self.kwargs['pk'])
        author = Person.objects.get(user=self.request.user)
        if 'Print' in competition.type.type:
            print = True
        else:
            print = False
        return {'competition': competition, 'author': author, 'print': print }
    
    def get_form_kwargs(self):
        kwargs = super(EnterCompetitionView, self).get_form_kwargs()
        kwargs.update({'pk': self.kwargs['pk']})  # to pass id to form
        kwargs['source_view'] = 'enter_competition'  # Indicate the source view
        return kwargs

    # Validation of photo done in the form
    def form_valid(self, form):
        # Get competition so we can add the image to it
        competition = Competition.objects.get(id=self.kwargs['pk'])
        image = form.save()
        image.competitions.add(competition)
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['competition'] = Competition.objects.get(id=self.kwargs['pk'])
        return context

class ViewEntriesView(LoginRequiredMixin, TemplateView):
    login_url = "accounts/login/"
    redirect_field_name = "next"
    template_name = 'main/view_entries.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['competition'] = Competition.objects.get(id=self.kwargs['competition_id'])
        images = context['competition'].images.all()
        image_index = []
        for image in images:
            image_index.append(image.id)
        context['images'] = images
        context['image_index'] = image_index           
        return context
    
class ListEntriesView(LoginRequiredMixin, TemplateView):
    login_url = "accounts/login/"
    redirect_field_name = "next"
    template_name = 'main/entries_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['competition'] = Competition.objects.get(id=self.kwargs['competition_id'])
        context['images'] = context['competition'].images.all()
        return context

class MemberVotingView(LoginRequiredMixin, View):
    login_url = "accounts/login/"
    redirect_field_name = "redirect_to"

    def get(self, request, competition_id):
        try:
            competition = Competition.objects.get(pk=competition_id)
            images = competition.images.all()
            image_index = []
            for image in images:
                image_index.append(image.id)
                
            for index, item in enumerate(image_index):
                print(str(index) + " " + str(item))
                
            if competition.type.selection_not_places:
                vote_options = VoteOption.objects.filter(active=True, judge_only=False, exclusive=False)
            else:
                vote_options = VoteOption.objects.filter(active=True, judge_only=False, exclusive=True)
            voted_options = set(
                Vote.objects.filter(voter=request.user.person.member, competition=competition).values_list('vote', flat=True)
            )
            context = {
                'competition': competition,
                'images': images,
                'image_index': image_index,
                'vote_options': vote_options,
                'voted_options': voted_options,
            }
            return render(request, 'main/member_voting.html', context)
        except Competition.DoesNotExist:
            return redirect('events')

    def post(self, request, competition_id):
        try:
            competition = Competition.objects.get(pk=competition_id)
            check = None
            for vote_option_id, image_id in request.POST.items():
                # first item passed is middleware token so ignore it
                if vote_option_id != "csrfmiddlewaretoken":
                    # Get vote option from ID
                    vo = VoteOption.objects.get(id = vote_option_id)
                    if image_id.isdigit() and vote_option_id.isdigit():
                        # Make sure member hasn't voted in this comp already
                        check = Vote.objects.filter(competition = competition,
                                            voter = request.user.person.member,
                                            vote__id = vote_option_id)
                        if check and vo.exclusive:
                            messages.error(request, "You already voted in this competition")
                            return redirect('events')
                        else:
                            # All good so create votes
                            vote_option = VoteOption.objects.get(pk=vote_option_id)
                            if not vote_option.judge_only:
                                vote = Vote.objects.update_or_create(
                                    voter=request.user.person.member,
                                    competition=competition,
                                    image_id=image_id,
                                    vote=vote_option,
                                )   
                        check = None
            messages.success(request, "Votes lodged")
            return redirect('events_now', year=datetime.now().year )
        except (Competition.DoesNotExist, VoteOption.DoesNotExist):
            return redirect('events_now', year=datetime.now().year )

def user_has_permission(user):
    return user.has_perm("main.change_competition")

def count_votes(competition):

    # Get all the images for the given competition
    images = competition.images.all()

    # Calculate total points for each image in the competition
    image_points = {}
    for image in images:
        total_points = image.vote_set.aggregate(total_points=Sum('vote__points'))['total_points']
        image_points[image] = total_points or 0
    
    # Sort images based on total points in descending order
    sorted_images = sorted(image_points.items(), key=lambda x: x[1], reverse=True)
    
    # Initialize variables to keep track of positions and tied counts
    positions = {}
    current_position = 1
    tied_count = 0
    previous_votes = None
       
    # Iterate through sorted items to assign positions
    for index, (image, votes) in enumerate(sorted_images):
        if votes > 0:
            if votes != previous_votes:
                # If the current number of votes is different from the previous one,
                # update the current position and reset tied count
                current_position += tied_count
                tied_count = 0
            if current_position <= 6:
                # Assign position to the person
                positions[image] = current_position
            tied_count += 1
            previous_votes = votes
                
        # Assign awards to the top 6 scoring images
        # Create an Award instance for the images with positions
    for image, position in positions.items():
        if position == 1:
            awardtype = AwardType.objects.get(name = "1st place")
            award = Award.objects.create(image=image, type=awardtype, competition=competition)
        elif position == 2:
            awardtype = AwardType.objects.get(name = "2nd place")
            award = Award.objects.create(image=image, type=awardtype, competition=competition)
        elif position == 3:
            awardtype = AwardType.objects.get(name = "3rd place")
            award = Award.objects.create(image=image, type=awardtype, competition=competition)
        elif position == 4:
            awardtype = AwardType.objects.get(name = "4th place")
            award = Award.objects.create(image=image, type=awardtype, competition=competition)
        elif position == 5:
            awardtype = AwardType.objects.get(name = "5th place")
            award = Award.objects.create(image=image, type=awardtype, competition=competition)
        elif position == 6:
            awardtype = AwardType.objects.get(name = "6th place")
            award = Award.objects.create(image=image, type=awardtype, competition=competition)
    return 

@login_required
@user_passes_test(user_has_permission)
def count_up_votes(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)
    print(competition)
    count_votes(competition)
    url = reverse('competition_awards', kwargs={'pk': competition_id})
    return redirect(url)

 

# class JudgeJudgingView(LoginRequiredMixin, DetailView):
#     '''Slideshow and list of images in competition'''
#     login_url = "accounts/login/"
#     redirect_field_name = "redirect_to"
#     model = Competition
#     template_name = 'main/judge_viewing.html'

#     def dispatch(self, request, *args, **kwargs):
#         # Additional check to ensure that the judge is viewing their assigned competition
#         # also viewable by committee position holders (for debugging)
#         self.object = self.get_object()
#         position = Position.objects.filter(person = self.request.user.person)
#         if not position:
#             judge = Person.objects.get(user=self.request.user)
#             if judge != self.object.judge.person:
#                 raise Http404("Judge " + str(judge) + " Object " + str(self.object.judge) )
#         return super().dispatch(request, *args, **kwargs)
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['blurb'] = Blurb.objects.get(name = 'Judging').contents
#         return context
    
class JudgeNotesView(LoginRequiredMixin, TemplateView):
    '''Slideshow and list of images in competition'''
    login_url = "accounts/login/"
    redirect_field_name = "next"
    template_name = 'main/judge_notes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_id = self.kwargs.get('event_id')
        context['event'] = Event.objects.get(id = event_id)
        context['blurb'] = Blurb.objects.get(name = 'Judging').contents
        return context

class CompAwardsView(DetailView):
    '''This displays the images and awards for a competition.'''
    
    model = Competition
    template_name = 'main/compgallery.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images'] = Image.objects.filter(award__competition__id = self.kwargs['pk'],
                                                 award__type__display_award = True).distinct()
        # if no images don't try to count votes or get awards
        if not context['images']:
            return context
        context['member_awards'] = Award.objects.filter(competition__id = self.kwargs['pk'],
                                                        type__awarded_by__members = True
                                                        ).order_by('-type__points')
        '''if there are no member awards, count the votes and create the awards.'''
        if not context['member_awards']:
            '''check to make sure voting has closed.
            If it has closed count the votes, create the awards and add them to the context'''
            competition = context['competition']
            if timezone.make_naive(competition.judging_closes) < timezone.make_naive(timezone.now()):
                try:
                    count_votes(competition)
                    context['member_awards'] = Award.objects.filter(competition__id = self.kwargs['pk'],
                                                        type__awarded_by__members = True
                                                        ).order_by('-type__points')
                except:
                    pass            
        context['judge_awards'] = Award.objects.filter(competition__id = self.kwargs['pk'],
                                                        type__awarded_by__judge = True
                                                        ).order_by('-type__points')
        return context

class CompNightView(PermissionRequiredMixin, ListView):
    '''List of comps on a night, this page will just be used to launch the full screen slideshows on 
    competition nights.
    Queryset is all competitions this month.'''
    permission_required = "main.change_competition"
    model = Competition
    context_object_name = 'competitions'
    template_name = 'main/compnight.html'
    queryset = Competition.objects.filter(event__starts__month = datetime.now().month,
                                          event__starts__year = datetime.now().year )

class CompNightImagesView(PermissionRequiredMixin, DetailView):
    '''Slideshow of images in competition'''
    permission_required = "main.change_competition"
    model = Competition
    template_name = 'main/slideshow.html'

class AllCompsSlideshow(PermissionRequiredMixin, DetailView):
    '''Slideshow of images in competition'''
    permission_required = "main.change_competition"
    model = Event
    template_name = 'main/all_slideshow.html'
    
class CompNightJudgesView(PermissionRequiredMixin, DetailView):
    '''Slideshow of images in competition'''
    permission_required = "main.change_competition"
    model = Competition
    template_name = 'main/judge_slideshow.html'

class UploadPhotoView(LoginRequiredMixin, UpdateView):
    login_url = "accounts/login/"
    redirect_field_name = "redirect_to"
    model = Image
    form_class = PhotoForm
    template_name = 'main/add_photo.html'
    
    def get_success_url(self):
        return reverse('profile', kwargs={'pk': self.object.author.id })

class AddImagesToCompetitionView(FormMixin, ListView):
    model = Image
    template_name = 'main/add_images_to_comp.html'
    context_object_name = 'images'
    form_class = ImageForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        kwargs['source_view'] = 'add_images'  # Indicate the source view
        return kwargs
    
    def get_queryset(self):
        competition = get_object_or_404(Competition, pk=self.kwargs.get('pk'))
        # order by id so that numbered list matches order of entry
        # this is for print list and stickers on comp night 
        return competition.images.all().order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['competition'] = get_object_or_404(Competition, pk=self.kwargs.get('pk'))
        context['form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        competition = get_object_or_404(Competition, pk=self.kwargs.get('pk'))
        image = form.save(commit=False)
        image.save()
        competition.images.add(image)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('competition_add_images', kwargs={'pk': self.kwargs.get('pk')})
    
class JudgeAwardUpdateView(PermissionRequiredMixin, TemplateView):
    template_name = 'main/award_entries.html'
    permission_required = "main.change_competition"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        competition_id = self.kwargs.get('pk')
        competition = Competition.objects.get(pk=competition_id)
        images = competition.images.all().order_by('id')
        formset_data = []
        for image in images:
            award = Award.objects.filter(image=image, 
                                         competition=competition,
                                         type__awarded_by__judge = True).first()
            initial = {
                'title': image.title,
                'author': f"{image.author.firstname} {image.author.surname}",
                'image_id': image.id,
                'competition_id': competition_id,
                'award_type': award.type if award else None
            }
            formset_data.append(initial)
        formset = JudgeAwardFormSet(initial=formset_data)
        context['competition'] = competition
        context['formset'] = formset
        return context

    def post(self, request, *args, **kwargs):
        competition_id = self.kwargs.get('pk')
        competition = Competition.objects.get(pk=competition_id)
        formset = JudgeAwardFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                image_id = form.cleaned_data['image_id']
                award_type = form.cleaned_data['award_type']
                existing_award = None
                if award_type == None:
                # Delete existing award if it exists
                    awards = Award.objects.filter(
                                image_id=image_id,
                                competition=competition,
                                type__awarded_by__judge=True
                                )
                    for award in awards:
                        award.delete()
                else:
                    # Get existing award
                    existing_award = Award.objects.filter(
                    image_id=image_id,
                    competition=competition,
                    type__awarded_by__judge=True
                    ).first()
                    # remove any extra awards
                    if existing_award:
                        existing_award_id = existing_award.id
                    else:
                        existing_award_id = 0
                    awards = Award.objects.filter(
                                image_id=image_id,
                                competition=competition,
                                type__awarded_by__judge=True
                                ).exclude(
                                    id = existing_award_id
                                )
                    for award in awards:
                        award.delete()
                if existing_award:
                    # Update existing award
                    existing_award.type = award_type
                    existing_award.save()
                elif award_type:
                    # Create new award from the judge if there is not an existing award
                    Award.objects.create(
                        image_id=image_id,
                        competition=competition,
                        type=award_type
                    )
            # Redirect to a success URL
            return HttpResponseRedirect(reverse_lazy('competition_awards', kwargs={'pk': self.kwargs.get('pk')}))
        else:
            # If the formset is invalid, re-render the template with errors
            return self.render_to_response(self.get_context_data(formset=formset))

class MemberAwardUpdateView(PermissionRequiredMixin, TemplateView):
    template_name = 'main/award_entries.html'
    permission_required = "main.change_competition"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        competition_id = self.kwargs.get('pk')
        competition = Competition.objects.get(pk=competition_id)
        images = competition.images.all().order_by('id')
        formset_data = []
        for image in images:
            award = Award.objects.filter(image=image, 
                                         competition=competition,
                                         type__awarded_by__members = True).first()
            initial = {
                'title': image.title,
                'author': f"{image.author.firstname} {image.author.surname}",
                'image_id': image.id,
                'competition_id': competition_id,
                'award_type': award.type if award else None
            }
            formset_data.append(initial)
        formset = MemberAwardFormSet(initial=formset_data)
        context['competition'] = competition
        context['formset'] = formset
        return context

    def post(self, request, *args, **kwargs):
        competition_id = self.kwargs.get('pk')
        competition = Competition.objects.get(pk=competition_id)
        formset = MemberAwardFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                image_id = form.cleaned_data['image_id']
                award_type = form.cleaned_data['award_type']
                existing_award = None
                if award_type == None:
                # Delete existing award if it exists
                    Award.objects.filter(
                        image_id=image_id,
                        competition=competition,
                        type__awarded_by__members=True
                        ).delete()
                else:
                    # Get existing award
                    existing_award = Award.objects.filter(
                    image_id=image_id,
                    competition=competition,
                    type__awarded_by__members=True
                    ).first()
                if existing_award:
                    # Update existing award
                    existing_award.type = award_type
                    existing_award.save()
                elif award_type:
                    # Create new award from the judge if there is an award
                    Award.objects.create(
                        image_id=image_id,
                        competition=competition,
                        type=award_type
                    )
            # Redirect to a success URL
            return HttpResponseRedirect(reverse_lazy('competition_awards', kwargs={'pk': self.kwargs.get('pk')}))
        else:
            # If the formset is invalid, re-render the template with errors
            return self.render_to_response(self.get_context_data(formset=formset))


class AddToGalleryView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    '''The view to upload to event galleries, similar to competition upload but without rules'''
    login_url = "accounts/login/"
    redirect_field_name = "/"
    model = Image  
    form_class = ImageForm
    template_name = 'main/image_upload_form.html'
    success_url = '/events/' + str(datetime.now().year) + '/#today_bookmark'
    success_message = "Image Uploaded to Gallery"

    def get_initial(self):
        gallery = Gallery.objects.get(id=self.kwargs['gallery_id'])
        author = Person.objects.get(user=self.request.user)
        return {'gallery': gallery, 'author': author }
    
    def get_form_kwargs(self):
        kwargs = super(AddToGalleryView, self).get_form_kwargs()
        kwargs.update({'gallery_id': self.kwargs['gallery_id']})  # to pass id to form
        return kwargs

    # Validation of photo done in the form
    def form_valid(self, form):
        # Get gallery so we can add the image to it
        gallery = Gallery.objects.get(id=self.kwargs['gallery_id'])
        image = form.save()
        image.galleries.add(gallery)
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['gallery'] = Gallery.objects.get(id=self.kwargs['gallery_id'])
        return context

'''View which combines 3 forms to add info to User, Person and Member models in one go'''
def add_member(request):
    if request.method == "POST":
        uform = UserForm(request.POST, instance=User())
        pform = PersonForm(request.POST, instance=Person())
        mform = MemberForm(request.POST, instance=Member())
        if uform.is_valid() and pform.is_valid() and mform.is_valid():
            new_user = uform.save(commit=False)
            new_user.username = uform.cleaned_data['first_name'] + "_" + uform.cleaned_data['last_name']
            new_user = uform.save()
            new_person = pform.save(commit=False)
            new_person.user = new_user
            new_person.firstname = new_user.first_name
            new_person.surname = new_user.last_name
            new_person.save()
            new_member = mform.save(commit=False)
            new_member.person = new_person
            new_member.save()
        return HttpResponseRedirect(reverse_lazy('members'))
    else:
        uform = UserForm(instance=User())
        pform = PersonForm(instance=Person())
        mform = MemberForm(instance=Member())
    context = {'user_form': uform, 'person_form': pform, 'member_form': mform}
    return render(request, 'main/add_member.html', context)

class AnnualTotalsView(PermissionRequiredMixin, ListView):
    '''This page lists all people who have entered competitions and total points by year.'''
    permission_required = "main.change_competition"
    model = Person
    template_name = 'main/totals.html'
    
    def get_year(self):
        """Return the year for which this view should display data.
        year can be set in the url, if not set it defaults to this year"""
        try:
            year = self.kwargs["year"]
        except:
            year = datetime.now().year
        return year
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.get_year()
        if Award.objects.filter(competition__event__starts__year=year -1):
            context['previous_year'] = year - 1
        if Award.objects.filter(competition__event__starts__year=year +1):
            context['next_year'] = year + 1
        context['year'] = year

        # Assuming AwardType objects have unique names
        comp_types = CompetitionType.objects.filter(contributes_to_annual = True,
                                                    active = True)
        context['comp_types'] = comp_types
        # Get all people (Members only inlcudes current members and this needs to work for all
        # previous years too)
        members = Person.objects.all()

        # Initialize a dictionary to store points totals for each person
        points_totals = {}
        
        keyword_display_names = { 'print' : 'Print Award', 
                    'digital' : 'Digital Award',
                    'set' : 'Set Subject Award',
                    'mono' : 'Open Mono Award',
                    'colour' : 'Open Colour Award' }
        
        context['keyword_display_names'] = keyword_display_names
        
        # Iterate over members
        for member in members:
            # Initialize a dictionary to store points for each award type
          
            member_points = {}
            combined_award_totals = {display_name: 0 for keyword, display_name in keyword_display_names.items()}
            
            # Iterate over award types
            for comp_type in comp_types:
                # Calculate points from awards for the current member and comp type
                # Points from all awards in each comp type this year
                award_points = Award.objects.filter(image__author=member, 
                                                    competition__type=comp_type,
                                                    competition__event__starts__year=year
                                                    ).aggregate(total_points=Sum('type__points'))['total_points'] or 0
                # One point for every entry in a comp for the current member and comp type this year
                entry_points = Image.objects.filter(author=member, 
                                                    competitions__type=comp_type,
                                                    competitions__event__starts__year=year).count()
                member_points[comp_type.type] = award_points + entry_points
                
            for keyword, display_name in keyword_display_names.items():
                # Calculate points for the current member combining competition types for EOY trophies
                combined_award_points = Award.objects.filter(image__author=member, 
                                                    competition__type__type__icontains=keyword,
                                                    competition__event__starts__year=year
                                                    ).aggregate(total_points=Sum('type__points'))['total_points'] or 0
                combined_entry_points = Image.objects.filter(author=member, 
                                                    competitions__type__type__icontains=keyword,
                                                    competitions__event__starts__year=year).count()
                combined_award_totals[display_name] += combined_award_points + combined_entry_points
            
            grand_total = sum(member_points.values())          
            
            # Create array of points per member
            points_totals[member] = {'points': member_points, 'combined_awards': combined_award_totals, 'grand_total': grand_total}
            
            # Add member and their points totals to the dictionary, add to context if any points
            if grand_total > 0:
                context['points_totals'] =  points_totals

        # Now points_totals dictionary contains points totals for each member 

        return context

@login_required
def eoy_competition(request):
    current_year = timezone.now().year
    if "mono" in request.path:
        user_images = Image.objects.filter(
            author=request.user.person,
            competitions__event__starts__year=current_year,
            competitions__type__type__in=['Open Mono Digital', 'Set Digital']
        ).distinct()
        end_of_year_competition = Competition.objects.get(event__starts__year=current_year,
                                                          type__type="End of Year - Mono Digital")
    else:
        user_images = Image.objects.filter(
            author=request.user.person,
            competitions__event__starts__year=current_year,
            competitions__type__type__in=['Open Colour Digital', 'Set Digital']
        ).distinct()
        end_of_year_competition = Competition.objects.get(event__starts__year=current_year,
                                                          type__type="End of Year - Colour Digital")

    # Get the images already selected for the competition
    selected_images = end_of_year_competition.images.filter(author=request.user.person)
    selected_image_ids = selected_images.values_list('id', flat=True)

    if request.method == 'POST':
        form = ImageSelectionForm(user_images=user_images, user=request.user, competition=end_of_year_competition, data=request.POST)
        if form.is_valid():
            new_selected_images = form.cleaned_data['images']
            # Remove deselected
            for image in selected_images:
                if image not in new_selected_images:
                    end_of_year_competition.images.remove(image)
            
            # Add newly selected images
            for image in new_selected_images:
                if image not in selected_images:
                    end_of_year_competition.images.add(image)
            messages.success(request, 'Your images have been successfully updated for the EoY competition')
            return redirect('main-gallery')
    else:
        form = ImageSelectionForm(user_images, initial={'images': selected_images})

    return render(request, 'main/select_eoy_images.html', {
        'form': form,
        'competition': end_of_year_competition,
        'user_images': user_images,
        'selected_images': selected_images,  # Pass selected_images to the template
        'selected_image_ids': list(selected_image_ids)
    })

