from django.contrib import admin
from django.utils.timezone import localtime
from .models import *
from .forms import EventAdminForm

admin.site.site_header = "WACC Site Admin"

class HasCompetitionFilter(admin.SimpleListFilter):
    title = 'competition entered'
    parameter_name = 'has_competition'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Entered in competitions'),
            ('no', 'Not entered'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'yes':
            return queryset.filter(competitions__isnull=False).distinct()
        if value == 'no':
            return queryset.filter(competitions__isnull=True).distinct()
        return queryset
    
class HasEventImageFilter(admin.SimpleListFilter):
    title = 'Used as event image'
    parameter_name = 'has_event'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Used as an Event image'),
            ('no', 'Not used'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'yes':
            return queryset.filter(event__isnull=False).distinct()
        if value == 'no':
            return queryset.filter(event__isnull=True).distinct()
        return queryset


# Register your models here.)admin.site.register(Person)
    
admin.site.register(Blurb)

admin.site.register(Newsletter)

admin.site.register(Person)    

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [ "person", "joined", "current", "get_email", "get_mobile" ]
    list_filter = [ "current" ]

    @admin.display(description='Phone Number')
    def get_mobile(self, obj):
        return obj.person.mobile
    
    @admin.display(description='Email Address')
    def get_email(self, obj):
        try:
            return obj.person.user.email
        except:
            return

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ( "position", "person" )

@admin.register(Judge)
class JudgeAdmin(admin.ModelAdmin):
    list_display = [ "person", "get_mobile", "get_email", "current" ]
    list_filter = [ "current" ]
    
    @admin.display(description='Phone Number')
    def get_mobile(self, obj):
        return obj.person.mobile
    
    @admin.display(description='Email Address')
    def get_email(self, obj):
        try:
            return obj.person.user.email
        except:
            return
     
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    def competitions_list(self, obj):
        return ", ".join(str(c) for c in obj.competitions.all())
    competitions_list.short_description = 'Competitions'
    search_fields = [
        'title',
        'author__surname',
        'id',
        'competitions__event__name',
        'competitions__subject__subject',
        'competitions__type__type'
    ]
    date_hierarchy = 'competitions__event__starts'
    list_display = [ 'id', 'title', 'print','author', 'photo', 'competitions_list']
    ordering = ['-competitions__event__starts']
    list_filter = [HasCompetitionFilter, HasEventImageFilter, 'competitions__event__starts']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    ordering = ['-starts']
    date_hierarchy = 'starts'
    list_display = [ "name", "local_starts", "local_ends" ]

    def local_starts(self, obj):
        local_time = localtime(obj.starts)
        return local_time.strftime('%Y-%m-%d %H:%M:%S')
    local_starts.short_description = 'Start Time (Local)'
    local_starts.admin_order_field = 'starts'

    def local_ends(self, obj):  
        return localtime(obj.ends).strftime('%Y-%m-%d %H:%M:%S')  
    local_ends.short_description = 'End Time (Local)'  
    local_ends.admin_order_field = 'ends'

    def hide_from_members_until_local(self, obj):  
        return localtime(obj.hide_from_members_until).strftime('%Y-%m-%d %H:%M:%S')  
    hide_from_members_until_local.short_description = 'Hide from Members Until (Local)'  
    hide_from_members_until_local.admin_order_field = 'hide_from_members_until'


admin.site.register(Rule)
admin.site.register(CompetitionType)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = [ "year", "subject" ]
    list_filter = [ 'year' ]

@admin.register(Competition)
class CompAdmin(admin.ModelAdmin):
    raw_id_fields = ['images']
    date_hierarchy = 'judging_closes'
    search_fields = [ 'subject__subject' ]
    list_display = [ "__str__", "judge", "open_for_entries_local", "entries_close_local", "open_for_judging_local", "judging_closes_local" ]

    def open_for_entries_local(self, obj):  
        return localtime(obj.open_for_entries).strftime('%Y-%m-%d %H:%M:%S')  
    open_for_entries_local.short_description = 'Open for Entries (Local)'  
    open_for_entries_local.admin_order_field = 'open_for_entries'

    def entries_close_local(self, obj):  
        return localtime(obj.entries_close).strftime('%Y-%m-%d %H:%M:%S')  
    entries_close_local.short_description = 'Entries Close (Local)'  
    entries_close_local.admin_order_field = 'entries_close'

    def open_for_judging_local(self, obj):  
        return localtime(obj.open_for_judging).strftime('%Y-%m-%d %H:%M:%S')  
    open_for_judging_local.short_description = 'Open for Judging (Local)'  
    open_for_judging_local.admin_order_field = 'open_for_judging'

    def judging_closes_local(self, obj):  
        return localtime(obj.judging_closes).strftime('%Y-%m-%d %H:%M:%S')  
    judging_closes_local.short_description = 'Judging Closes (Local)'  
    judging_closes_local.admin_order_field = 'judging_closes'

admin.site.register(Awarder)    

@admin.register(AwardType)
class AwardTypeAdmin(admin.ModelAdmin):
    list_display = [ "name", "awarded_by", "points", "active" ]

@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    date_hierarchy = 'competition__event__starts'
    search_fields = [ 'image__title', 'image__author__surname' ]

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    date_hierarchy = 'event__starts'
    list_display = [ "__str__", "event", "public_after_local", "member_upload_from_local", "member_upload_until_local"]

    def public_after_local(self, obj):  
        return localtime(obj.public_after).strftime('%Y-%m-%d %H:%M:%S')  
    public_after_local.short_description = 'Public After (Local Time)'  
    public_after_local.admin_order_field = 'public_after'

    def member_upload_from_local(self, obj):  
        return localtime(obj.member_upload_from).strftime('%Y-%m-%d %H:%M:%S')  
    member_upload_from_local.short_description = 'Member Upload From (Local Time)'  
    member_upload_from_local.admin_order_field = 'member_upload_from'

    def member_upload_until_local(self, obj):  
        return localtime(obj.member_upload_until).strftime('%Y-%m-%d %H:%M:%S')  
    member_upload_until_local.short_description = 'Member Upload Until (Local Time)'  
    member_upload_until_local.admin_order_field = 'member_upload_until'


admin.site.register(ImageCompetitionComment)
admin.site.register(VoteOption)
admin.site.register(ResourceGroup)

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = [ "__str__", "group", "visibility"]

@admin.register(PrintVote)
class PrintVoteAdmin(admin.ModelAdmin):
    date_hierarchy = 'competition__event__starts'

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    date_hierarchy = 'competition__event__starts'

@admin.register(PrintImage)
class PrintImageAdmin(admin.ModelAdmin):
    date_hierarchy = 'competition__event__starts'