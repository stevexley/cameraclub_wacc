from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

from main.models import Event, Competition, Member
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Send event and competition reminder emails"

    def handle(self, *args, **kwargs):

        today = timezone.localdate()
        in_three_days = today + timedelta(days=3)

        members = Member.objects.filter(current=True)

        # Events happening today
        events_today = Event.objects.filter(starts__date=today)

        for event in events_today:
            if not "No " in event.name:

                subject = f"Reminder: WACC {event.name} tonight"
                message = f"""{event.name} starts at {event.starts}
                {event.description}"""

                for member in members:
                    send_mail(
                        subject,
                        message,
                        None,
                        [member.person.user.email],
                        fail_silently=False
                    )

        # Competitions closing soon
        comps_closing = Event.objects.filter(competition__entries_closed__date=in_three_days,).distinct()

        for event in comps_closing:
            comp_blurb = "If you haven't already, time is running out to enter this month's digital competitions."
            if not "No " in event.name:
                subject = f"Reminder: Entries closing for WACC {event.name}"
                for comp in event.competition_set.all():
                    if "igital" in comp.type.type:
                        comp_blurb = comp_blurb + f"""
                        {comp.subject.subject}
                        {comp.subject.description}

                        """
                message = f"""Entries close on {event.competitions.entries_close.first()}
                            
                            {comp_blurb}
                            """

                for member in members:
                    if member.current:
                        send_mail(
                            subject,
                            message,
                            None,
                            [member.person.user.email],
                            fail_silently=False
                    )