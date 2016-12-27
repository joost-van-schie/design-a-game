#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""

from api import HangmanApi

from google.appengine.api import app_identity, mail

from models import User

import webapp2


class SendReminderEmail(webapp2.RequestHandler):

    def get(self):
        """Send a reminder email to users with active games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None).filter(User.active_games > 0)
        for user in users:
            subject = 'This is a reminder!'
            body = 'Hello {}, you have active games, please make a move!'.format(
                user.name)
            # This will send test emails, the arguments to send_mail are:
            # from, to, subject, body
            mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user.email,
                           subject,
                           body)


class UpdateAverageMovesRemaining(webapp2.RequestHandler):

    def post(self):
        """Update game listing announcement in memcache."""
        HangmanApi._cache_average_attempts()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_attempts', UpdateAverageMovesRemaining),
], debug=True)
