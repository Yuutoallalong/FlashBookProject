from django.shortcuts import render, redirect
from homepage.models import *
from django.db.models import Min,Max

# Create your views here.

def flashcard(request,folder_id):
    username = request.user

    referrer = request.META.get('HTTP_REFERER', None)

    if (referrer and 'community' in referrer) or request.session.get('came_from_community'):
        user = User.objects.get(user_id=request.session.get('user_id_admin'))
        folder_id = request.session.get('folder_id_admin')
        request.session['came_from_community'] = True
        time_value = 10
    else:
        user = User.objects.get(user=username)
        time_value = request.GET.get('time', request.session.get('time_value'))
        
    folder = Folder.objects.get(user=user,folder_id=folder_id)
    # time_value = request.GET.get('time', request.session.get('time_value'))

    request.session['time_value'] = time_value
    if request.session.get('came_from_answer'):
        time_value = None
    
    min_word_id = Word.objects.filter(user=user, folder=folder).aggregate(Min('word_id'))['word_id__min']

    max_play_time = Highscore.objects.filter(user=user, folder=folder,game_id=1).aggregate(Max('play_time'))['play_time__max']

    default_word_id = min_word_id if min_word_id is not None else 1

    currentWordId = request.session.get('currentWordId', default_word_id)
    request.session['currentWordId'] = currentWordId

    word = Word.objects.filter(user=user, folder=folder, word_id=currentWordId).first()
    
    if referrer and "flashcard" in referrer:
        highscore = Highscore.objects.get(
            user=user,
            folder=folder,
            game_id=1,
            play_time = max_play_time
        )
    else:
        highscore = Highscore.objects.create(
            user=user,
            folder=folder,
            game_id=1,
            score = 0
        )
        request.session['answered'] = False

    playtime = highscore.play_time

    # Check if the user wants to see the meaning
    showMeaning = request.session.get('showMeaning', False)

    # Prepare the context
    context = {
        'highscore': highscore,
        'user': user,
        'word': word.word if word and not showMeaning else word.meaning if word else None,
        'showMeaning': showMeaning,
        'folder':folder,
        'playtime':playtime,
        'time_value':time_value,
    }
    # request.session['answered'] = False

    return render(request, 'flashcard.html', context)


def correct_answer(request, folder_id, playtime):
    username = request.user

    if request.session.get('came_from_community'):
        user = User.objects.get(user_id=request.session.get('user_id_admin'))
        folder = Folder.objects.get(user=request.session.get('user_id_admin'),folder_id=request.session.get('folder_id_admin'))
    else:
        user = User.objects.get(user=username)
        folder = Folder.objects.get(user=user, folder_id=folder_id)

    # Retrieve or create Highscore for the user and folder
    highscore = Highscore.objects.get(
        user=user,
        folder=folder,
        game_id=1,
        play_time=playtime
    )

    if not request.session.get('answered', False):
        # Increment score if user has not already answered
        highscore.score += 1
        highscore.save()
        
        # for public game
        if request.session.get('came_from_community'):
            if highscore.score % 3 == 0:
                user_add_credits = User.objects.get(user=username)
                user_add_credits.credits += 10
                user_add_credits.save()

        # Mark that the user has answered
        request.session['answered'] = True

    # Set the session to show the meaning after either "correct" or "wrong"
    request.session['showMeaning'] = True
    # Redirect to flashcard page
    request.session['came_from_answer'] = True
    # request.session['time_value'] = None

    return redirect('flashcard', folder_id=folder.folder_id)


def wrong_answer(request, folder_id):
    username = request.user
    user = User.objects.get(user=username)
    if request.session.get('came_from_community'):
        user = User.objects.get(user_id=request.session.get('user_id_admin'))
        folder = Folder.objects.get(user=request.session.get('user_id_admin'),folder_id=request.session.get('folder_id_admin'))
    else:
        user = User.objects.get(user=username)
        folder = Folder.objects.get(user=user, folder_id=folder_id)
    
    # Set time to 0 when the user clicks "Wrong"
    # request.session['time_value'] = None

    # Set the session to show the meaning after either "correct" or "wrong"
    request.session['showMeaning'] = True

    request.session['came_from_answer'] = True
    # request.session['time_value'] = None

    # Redirect to flashcard page
    return redirect('flashcard', folder_id=folder.folder_id)


def next_word(request, folder_id, playtime):
    username = request.user
    user = User.objects.get(user=username)
    if request.session.get('came_from_community'):
        user = User.objects.get(user_id=request.session.get('user_id_admin'))
        folder = Folder.objects.get(user=request.session.get('user_id_admin'),folder_id=request.session.get('folder_id_admin'))
    else:
        user = User.objects.get(user=username)
        folder = Folder.objects.get(user=user, folder_id=folder_id)
    currentWord = request.session.get('currentWordId')

    # time_value = request.GET.get('time', 10)  # Retrieve the initial time value

    # Set time_value back to the initial value when "Next" is pressed
    # request.session['time_value'] = time_value

    nextWord = Word.objects.filter(user=user, folder=folder, word_id=currentWord + 1).first()

    request.session['currentWordId'] = request.session.get('currentWordId') + 1

    if not nextWord:
        request.session['showMeaning'] = False
        del request.session['currentWordId']
        return redirect('finish', folder_id=folder.folder_id)
    
    # Set the current word in the session for the next call
    request.session['currentWordId'] = nextWord.word_id if nextWord else currentWord
    
    # Reset session to show the word, not the meaning, after moving to the next word
    request.session['answered'] = False
    request.session['showMeaning'] = False

    request.session['came_from_answer'] = False
    
    return redirect('flashcard', folder_id=folder.folder_id)


def finish(request,folder_id):
    del request.session['user_id_admin']
    del request.session['folder_id_admin']
    request.session['came_from_community'] = False
    return render(request,'finish.html')






