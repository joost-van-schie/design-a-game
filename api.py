# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import random

import endpoints

from google.appengine.api import memcache

from google.appengine.api import taskqueue

from models import Game, Score, User

from protorpc import messages, remote

from models import StringMessage, NewGameForm, GameForm, GuessCharactarForm,\
    GuessAnswerForm, ScoreForms, GameForms, HighScoresForm, UserForms
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
GUESS_CHARACTAR_REQUEST = endpoints.ResourceContainer(
    GuessCharactarForm,
    urlsafe_game_key=messages.StringField(1),)
GUESS_ANSWER_REQUEST = endpoints.ResourceContainer(
    GuessAnswerForm,
    urlsafe_game_key=messages.StringField(1),)
CANCEL_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
HIGH_SCORES_REQUEST = endpoints.ResourceContainer(HighScoresForm)

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'


@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Game API"""

    @endpoints.method(request_message=CANCEL_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/cancel/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """Cancels a game."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)

        if game:
            if game.game_over:
                return StringMessage(message='Game already over!')
            else:
                game.key.delete()
                return StringMessage(message='Game deleted!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to do a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')

        words = ("python", "hangman", "easy",
                 "difficult", "answer", "xylophone")
        answer = random.choice(words)

        game = Game.new_game(user.key, answer, request.attempts)
        user.active_games += 1
        user.put()

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Hangman!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Returns the game history."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            msg = ' '.join(str(x) for x in game.history)
            return StringMessage(message=msg)
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GUESS_CHARACTAR_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='guess_character',
                      http_method='PUT')
    def guess_character(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        user = game.user.get()

        # Check if game isn't already over
        if game.game_over:
            return game.to_form('Game already over!')

        # Check if guess isn't longer then one character
        if len(request.guess) > 1:
            return game.to_form('One character per turn')

        # Decrease remaining attempts
        game.attempts_remaining -= 1

        # Look for character positions
        character_positions = [i for i, ltr in enumerate(
            game.answer) if ltr == request.guess]

        if not character_positions:
            msg = "No '%s' here!" % request.guess
        else:
            msg = "Character is found on position %s." % ' and '.join(
                str(x + 1) for x in character_positions)

        msg = unicode(msg)
        guess = unicode(request.guess)

        if game.attempts_remaining < 1:
            msg = msg + ' Game over!'
            game.end_game(False)
            user.score -= 1
            user.active_games -= 1
            user.put()
            game.add_game_history(msg, guess)
            return game.to_form(msg)
        else:
            game.put()
            game.add_game_history(msg, guess)
            return game.to_form(msg)

    @endpoints.method(request_message=GUESS_ANSWER_REQUEST,
                      response_message=GameForm,
                      path='game/answer/{urlsafe_game_key}',
                      name='guess_answer',
                      http_method='PUT')
    def guess_answer(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        user = game.user.get()
        guess = unicode(request.guess)

        # Check if game isn't already over
        if game.game_over:
            return game.to_form('Game already over!')

        # Decrease remaining attempts
        game.attempts_remaining -= 1

        if game.attempts_remaining < 1:
            msg = 'Game over!'
            game.end_game(False)
            game.add_game_history(msg, guess)
            user.score -= 1
            user.active_games -= 1
            user.put()
            return game.to_form(msg)
        elif request.guess == game.answer:
            msg = 'You win!'
            game.end_game(True)
            game.add_game_history(msg, guess)
            user.score += 1
            user.active_games -= 1
            user.put()
            return game.to_form(msg)
        else:
            msg = 'Wrong answer, try again'
            game.put()
            game.add_game_history(msg, guess)
            return game.to_form(msg)

    @endpoints.method(response_message=UserForms,
                      path='users',
                      name='get_users',
                      http_method='GET')
    def get_users(self, request):
        """Return all users"""
        return UserForms(items=[user.to_form() for user in User.query()])

    @endpoints.method(response_message=UserForms,
                      path='get_user_rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Return all users orderd by score"""
        users = User.query().order(-User.score)
        return UserForms(items=[user.to_form() for user in users])

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=HIGH_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='high_scores',
                      name='get_high_scores',
                      http_method='POST')
    def get_high_scores(self, request):
        """Return high-scores"""
        high_scores_query = Score.query(Score.won == True).order(Score.guesses)
        high_scores = high_scores_query.fetch(request.number_of_results)
        return ScoreForms(items=[score.to_form() for score in high_scores])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all games by created by the provided player"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        games = Game.query(Game.user == user.key)
        return GameForms(items=[game.to_form('') for game in games])

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                            for game in games])
            average = float(total_attempts_remaining) / count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))


api = endpoints.api_server([HangmanApi])
