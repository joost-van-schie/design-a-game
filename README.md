#Design a game

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
 
 
 
##Game Description:
Hangman is a simple guessing game. Each game begins with a random 'word' and a maximum number of 'attempts'. 'Guesses' are sent to the `guess_character`  endpoint which will reply
with either: 'No 'a' here!', 'Character is found on position 1', 'One character per turn, or 'game over' (if the maximum number of attempts is reached).

The player may, at any time, attempt to guess the whole word. If the word is correct, the game is over and the guesser wins. This is possible with the endpoint `guess_answer`

Many different Hangman games can be played by many different Users at any given time. Each game can be retrieved or played by using the path parameter `urlsafe_game_key`.

If the player wins a game the userscore is increased by one. If the player loses a game the userscore is decreased by one.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **cancel_game**
    - Path: 'game/cancel/{urlsafe_game_key}'
    - Method: POST
    - Parameters: urlsafe_game_key
    - Returns: Message confirming deletion of the Game.
    - Description: Delete the game. Will raise a NotFoundException if the Game does not exist.

 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.

 - **get_average_attempts_remaining**
    - Path: 'games/average_attempts'
    - Method: GET
    - Parameters: None
    - Returns: String with average attempts
    - Description: Returns string with average attempts
    
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.

 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: String with all moves and results from a game.
    - Description:  Return string with all moves and results from a game.
    
 - **get_high_scores**
    - Path: 'high_scores'
    - Method: GET
    - Parameters: number_of_results
    - Returns: ScoreForms.
    - Description: Returns high-scores in the database ordered by guesses.

 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).

 - **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: user_name, email (optional)
    - Returns: GameForms from all games created by the provided player.
    - Description: Returns all games created by the provided player.

 - **get_user_rankings**
    - Path: 'get_user_rankings'
    - Method: GET
    - Parameters: none
    - Returns: UserForms.
    - Description: Returns all users ordered by score.
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.

 - **get_users**
    - Path: 'users'
    - Method: GET
    - Parameters: none
    - Returns: UserForms.
    - Description: Returns all users.

 - **guess_answer**
    - Path: 'game/answer/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.

 - **guess_character**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.

 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, attempts
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an existing user - will raise a NotFoundException if not. Also adds a task to a task queue to update the average moves remaining for active games.

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **NewGameForm**
    - Used to create a new game (user_name, min, max, attempts)
 - **GuessCharacterForm**
    - Inbound make move form (guess).
  - **GuessAnswerForm**
    - Inbound make move form (guess).
 - **HighScoresForm**
    - Representation of a completed game's high-score (number_of_results).
 - **UserForm**
    - Representation of user (name, email, score).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **GameForms**
    - Multiple GameForm container.
 - **UserForms**
    - Multiple UserForm container.
 - **StringMessage**
    - General purpose String container.