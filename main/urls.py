from django.urls import path, include
from .views import *
from .utils import *
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
 
urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('members', MemberListView.as_view(), name='members'),
    path('members/add', add_member, name='add_member'),
    path('', MainGalleryView.as_view(), name = 'main-gallery'),
    path('aboutus', AboutUsView.as_view(), name='aboutus'),
    path('newsletters/<int:year>/', NewslettersView.as_view(), name='news'),
    path('newsletters/add/', NewsletterCreateView.as_view(), name='add_newsletter'),
    path('newsletters/edit/<int:pk>/', NewsletterUpdateView.as_view(), name='edit_newsletter'),
    path('profile/<int:pk>', ProfileView.as_view(), name='profile'),
    path('events/<int:year>/', EventsView.as_view(), name='events'),
    path('events/<int:year>/#today_bookmark', EventsView.as_view(), name='events_now'),
    path('events/', EventsView.as_view(), name='events'),
    path('event/<int:pk>', EventDetailView.as_view(), name='event'),
    path('event/<int:pk>/AddFile', UploadEventFileView.as_view(), name='event_add_file'),
    path('gallery/<int:gallery_pk>/zip', zip_gallery, name='gallery-zip'),
    path('gallery/<int:in_gallery_pk>/transfer', copy_to_gallery, name='copy_to_gallery'),
    path('create_events', createwaccevents, name='create-events'),
    path('move_events', move_imported_events, name='move-events'),
    path('1st_events', move_comps_to_1st, name='1st-events'),
    path('import_pics', import_pics, name='import_pics'),
    path('cleanup_photos', cleanup_photos, name='cleanup_photos'),
    path('set_comp_images', set_comp_images, name='set_comp_images'),
    path('event/<int:event_id>/create_comp', CompCreateView.as_view(), name='create_comp'),
    path('event/<int:event_id>/create_compnight', setup_competition_night, name='create_compnight'),
    path('event/<int:pk>/create_gallery', GalleryCreateView.as_view(), name='gallery_create'),
    path('event/<int:event_id>/judge_notes/', JudgeNotesView.as_view(), name='judge_notes'),
    path('event/<int:pk>/slideshow/', AllCompsSlideshow.as_view(), name='all_slideshow'),
    path('competitions/<int:comp_pk>/award_gold_dist/<image_pk>', award_gold_dist, name='award_gold_dist'),
    path('competitions/<int:comp_pk>/award_gold/<image_pk>', award_gold, name='award_gold'),
    path('competitions/<int:comp_pk>/award_silver/<image_pk>', award_silver, name='award_silver'),
    path('competitions/<int:comp_pk>/award_bronze/<image_pk>', award_bronze, name='award_bronze'),
    path('competitions/<int:comp_pk>/award_merit/<image_pk>', award_merit, name='award_merit'),
    path('competitions/<int:pk>/enter/', EnterCompetitionView.as_view(), name='enter_competition'),
    path('competitions/<int:comp_id>/remove/<int:img_id>', remove_entry, name='remove_entry'),
    path('competitions/<int:competition_id>/vote/', MemberVotingView.as_view(), name='competition_vote'),
    path('competitions/<int:competition_id>/view/', ViewEntriesView.as_view(), name='view_entries'),
    path('competitions/<int:competition_id>/list/', ListEntriesView.as_view(), name='list_entries'),
    path('competitions/<int:competition_id>/count/', count_up_votes, name='count_votes'),
    path('competitions/<int:pk>/addimages/', AddImagesToCompetitionView.as_view(), name='competition_add_images'),
#    path('competitions/<int:pk>/judge/', JudgeJudgingView.as_view(), name='competition_judge'),
    path('competitions/<int:pk>/awards/', CompAwardsView.as_view(), name='competition_awards'),
    path('competitions/<int:year>/totals/', AnnualTotalsView.as_view(), name='totals'),
    path('competitions/night/' , CompNightView.as_view(), name='compnight'),
    path('competitions/<int:pk>/slideshow/', CompNightImagesView.as_view(), name='slideshow'),
    path('competitions/<int:pk>/judge_slideshow/', CompNightJudgesView.as_view(), name='judge_slideshow'),
    path('competitions/<int:pk>/edit_judge_awards/', JudgeAwardUpdateView.as_view(), name='edit_judge_awards'),
    path('competitions/<int:pk>/edit_member_awards/', MemberAwardUpdateView.as_view(), name='edit_member_awards'),
    path('competitions/<int:comp_pk>/create_zip', zip_comp_images, name='create_zip'),
    path('images/<int:pk>/addphoto', UploadPhotoView.as_view(), name='upload_photo'),
    path('add-to-gallery/<int:pk>', AddToGalleryView.as_view(), name='add_to_gallery'),
#    path('end-of-year-entry/', EndOfYearEntryView.as_view(), name='end_of_year_entry'),
    path('end-of-year-entry/mono', eoy_competition, name='end_of_year_entry_mono'),
    path('end-of-year-entry/colour', eoy_competition, name='end_of_year_entry_colour'),
    path('end-of-year-entry/mono_prints', eoy_competition_prints, name='end_of_year_entry_mono_prints'),
    path('end-of-year-entry/colour_prints', eoy_competition_prints, name='end_of_year_entry_colour_prints'),
    path('end-of-year-entry/mono_labels', eoy_competition_labels, name='end_of_year_entry_mono_labels'),
    path('end-of-year-entry/colour_labels', eoy_competition_labels, name='end_of_year_entry_colour_labels'),
    path('resources', ResourcesView.as_view(), name="resources"),
    path('resources/<int:resource_id>/', download_resource, name='download_resource'),
    path("ajax/image-search/", image_search, name="image_search"),
#    path('image', views.image, name='image')
]
 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()