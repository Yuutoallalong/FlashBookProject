from django.shortcuts import render
from homepage.models import User, Highscore, Folder, Word
from random import choice,sample
from django.db.models import Max

def word_guess_view(request, folder_id):
    username = request.user

    referrer = request.META.get('HTTP_REFERER', None)

    if (referrer and 'community' in referrer) or request.session.get('came_from_community'):
        user = User.objects.get(user_id=request.session.get('user_id_admin'))
        folder_id = request.session.get('folder_id_admin')
        request.session['came_from_community'] = True
    else:
        user = User.objects.get(user=username)

    folder = Folder.objects.get(user=user, folder_id=folder_id)
    words = Word.objects.filter(user=user, folder=folder)
    difficulty = request.GET.get('difficulty')
    
    guesses = request.session.get('guesses', [])
    hint_message = ""
    
    if 'word_id' not in request.session: #choose word for new session
        word = choice(words)
        request.session['word_id'] = word.word_id
        guesses = [] # makes guess characlist empty for new sesion

        if difficulty == "easy":
            prefill_count = max(1, len(word.word) // 2)  # Prefill ~50%
            unique_chars = set(word.word.lower())  # Get unique characters
            prefill_count = min(prefill_count, len(unique_chars))  # Ensure we don't sample more than available
            guesses = sample(list(unique_chars), prefill_count)
            request.session['hearts_left'] = 6
        elif difficulty == "normal":
            prefill_count = max(1, len(word.word) // 4)  # Prefill ~25%
            unique_chars = set(word.word.lower())
            prefill_count = min(prefill_count, len(unique_chars))
            guesses = sample(list(unique_chars), prefill_count)
            request.session['hearts_left'] = 6
        elif difficulty == "hard":
            guesses = []  # No prefilled characters
            request.session['hearts_left'] = 4  # Reduce initial hearts_left for hard mode


        request.session['guesses'] = guesses # update session guess detail
    else:
        word = Word.objects.get(
        word_id=request.session['word_id'],
        user=user,
        folder=folder
        )

    meaning = word.meaning
    
    hearts_left = request.session.get('hearts_left')

    # Process guess
    if request.method == "POST":

        if 'guess' in request.POST:  # Handle guesses
            guesses, hearts_left = process_guess(request, word, guesses, request.session.get('hearts_left'))
            request.session['guesses'] = guesses
            request.session['hearts_left'] = hearts_left

        elif 'hint_request' in request.POST:  # Handle hint requests
            hint, guesses = get_hint(user, word, guesses)
            if hint:
                hint_message = f"Hint: The letter '{hint}' has been revealed!"
                request.session['guesses'] = guesses
            else:
                hint_message = "Not enough hint!"
                
            user.refresh_from_db()
    
    display_word = get_display_word(word, guesses) # Call display_word method
    request.session['display_word'] = display_word

    # Check if the game is over
    game_end = False
    message = ""
    
    if "_" not in display_word:  # If no blanks, the word is fully guessed
        game_end = True
        message = "Congratulations! You guessed the word!"
    elif hearts_left == 0:  # If the hearts_left is 0, the game is over
        game_end = True
        message = f"You lost! The word was '{word.word}'."

    max_play_time = Highscore.objects.filter(user=user, folder=folder,game_id=2).aggregate(Max('play_time'))['play_time__max']

    if referrer and "wordguess" in referrer:
        highscore = Highscore.objects.get(
            user=user,
            folder=folder,
            game_id=2,
            play_time = max_play_time
        )
    else:
        highscore = Highscore.objects.create(
            user=user,
            folder=folder,
            game_id=2,
            score = 0
        )

    playtime = highscore.play_time

    if game_end:
        request.session['game_end'] = True
        # Update or create highscore at the end of the game
        if hearts_left != 0:
            update_highscore(user, folder, playtime)
            highscore.refresh_from_db()

            if request.session.get('came_from_community'):
                if highscore.score % 3 == 0:
                    user_add_credits = User.objects.get(user=username)
                    user_add_credits.credits += 10
                    user_add_credits.save()

        #reset session
        request.session.pop('word_id', None)
        request.session.pop('guesses', None)
        request.session.pop('hearts_left', None)

    else:
        request.session['game_end'] = False

    hearts_range = range(hearts_left)

    # Prepare the context for the template
    context = {
        'highscore': highscore,
        'display_word': display_word,
        'game_end': game_end,
        'message': message,
        'hint_message': hint_message,
        'guesses': guesses,
        'hearts_left': hearts_left,
        'user': user,
        'hint_ava': user.hint_ava,
        'word': word,
        'meaning': meaning,
        'folder': folder,
        'difficulty' : difficulty,
        'hearts_range' : hearts_range
    }

    return render(request, 'wordguess/wordGuess.html', context) #render site with parameter from context

def process_guess(request, word, guesses, hearts_left):
    guess = request.POST.get('guess','').lower()  # Get the guess and convert it to lowercase
    word_lower = word.word.lower()

    if guess and len(guess) == 1 and guess.isalnum():  # Check if there's an guess input (alphanumeric)length = 1
        if guess not in guesses:  # Only process the guess if it's a new character
            guesses.append(guess)
            request.session['guesses'] = guesses  # Save the guesses list back to the session

            # Check if the guess is incorrect, decrease hearts_left
            if guess not in word_lower:
                hearts_left -= 1
                request.session['hearts_left'] = hearts_left

    return guesses, hearts_left

def update_highscore(user, folder,playtime):
    highscore = Highscore.objects.get(
        user=user,
        folder=folder,
        game_id=2,
        play_time=playtime
    )
    highscore.score += 1
    highscore.save()

def get_display_word(word, guesses):
    word_lower = word.word.lower()
    return " ".join([char if char in guesses else "_" for char in word_lower])  # Display _ _ _ _ _ ...

def get_hint(user, word, guesses):

    if user.hint_ava > 0:
        user.hint_ava -= 1
        user.save()

        remaining_chars = set(word.word.lower()) - set(guesses)
        if remaining_chars:
            hint = remaining_chars.pop()  # Get a random unrevealed character
            guesses.append(hint)
            return hint, guesses
    return None, guesses











