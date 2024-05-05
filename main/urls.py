from django.urls import path, include
from .views import *
from .utils import createwaccevents, move_imported_events, move_comps_to_1st, award_gold, award_silver, award_bronze, import_pics, cleanup_photos
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
 
urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('members', MemberListView.as_view(), name='members'),
    path('', MainGalleryView.as_view(), name = 'main-gallery'),
    path('aboutus', AboutUsView.as_view(), name='aboutus'),
    path('newsletters/<int:year>/', NewslettersView.as_view(), name='news'),
    path('profile/<int:pk>', ProfileView.as_view(), name='profile'),
    path('events/<int:year>/', EventsView.as_view(), name='events'),
    path('events/', EventsView.as_view(), name='events'),
    path('event/<int:pk>', EventDetailView.as_view(), name='event'),
    path('event/<int:pk>/AddFile', UploadEventFileView.as_view(), name='event_add_file'),
    path('create_events', createwaccevents, name='create-events'),
    path('move_events', move_imported_events, name='move-events'),
    path('1st_events', move_comps_to_1st, name='1st-events'),
    path('import_pics', import_pics, name='import_pics'),
    path('cleanup_photos', cleanup_photos, name='cleanup_photos'),
    path('event/<int:event_id>/create_comp', CompCreateView.as_view(), name='create_comp'),
    path('event/<int:event_id>/create_compnight', setup_competition_night, name='create_compnight'),
    path('competitions/<int:comp_pk>/award_gold/<image_pk>', award_gold, name='award_gold'),
    path('competitions/<int:comp_pk>/award_silver/<image_pk>', award_silver, name='award_silver'),
    path('competitions/<int:comp_pk>/award_bronze/<image_pk>', award_bronze, name='award_bronze'),
    path('competitions/<int:pk>/enter/', EnterCompetitionView.as_view(), name='enter_competition'),
    path('competitions/<int:competition_id>/vote/', MemberVotingView.as_view(), name='competition_vote'),
    path('competitions/<int:pk>/addimages/', AddImagesToCompetitionView.as_view(), name='competition_add_images'),
    path('competitions/<int:pk>/judge/', JudgeJudgingView.as_view(), name='competition_judge'),
    path('competitions/<int:pk>/awards/', CompAwardsView.as_view(), name='competition_awards'),
    path('competitions/<int:year>/totals/', AnnualTotalsView.as_view(), name='totals'),
    path('competitions/night/' , CompNightView.as_view(), name='compnight'),
    path('competitions/<int:pk>/slideshow/', CompNightImagesView.as_view(), name='slideshow'),
    path('competitions/<int:pk>/judge_slideshow/', CompNightJudgesView.as_view(), name='judge_slideshow'),
    path('competitions/<int:pk>/edit_judge_awards/', JudgeAwardUpdateView.as_view(), name='edit_judge_awards'),
    path('competitions/<int:pk>/edit_member_awards/', MemberAwardUpdateView.as_view(), name='edit_member_awards'),
    path('images/<int:pk>/addphoto', UploadPhotoView.as_view(), name='upload_photo'),
    path('add-to-gallery/<int:gallery_id>', AddToGalleryView.as_view(), name='add_to_gallery'),
    
#    path('image', views.image, name='image')
]
 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()