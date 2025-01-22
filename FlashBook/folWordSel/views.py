from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.models import User
from homepage.models import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from io import BytesIO
import base64
from django.http import JsonResponse
import pandas as pd
import io
import random
from urllib.parse import urlencode
from django.urls import reverse
import chardet
# Create your views here.

def folder_view(request,noti="Looks like you don't have any folders yet. Let's add one to get started!"):
    #user = User.objects.get(user_id=request.session.get('user_id'))
    #folders = Folder.objects.filter(user=user)
    #return render(request,'folder.html',{'user':user,'folders':folders,'noti':noti})
    #def folder_view(request, noti="..."):
    auth_user = request.user  # Django's User model
    user = User.objects.get(user_id=request.session.get('user_id'))  # Your custom user
    folders = Folder.objects.filter(user=user)
    return render(request, 'folder.html', {
        'user': user,
        'auth_user': auth_user,
        'folders': folders,
        'noti': noti
    })

def word_view(request, folder_id, noti='This folder is empty. Start by adding words!'):
    auth_user = request.user
    user = User.objects.get(user_id=request.session.get('user_id'))
    folder = Folder.objects.get(user=user,folder_id=folder_id)
    words = Word.objects.filter(user=user,folder=folder)
    #return render(request,'word.html',{'words' : words,'folder':folder,'noti':noti})
    return render(request, 'word.html', {
        'auth_user': auth_user,
        'user': user,
        'folder': folder,
        'words': words,
        'noti': noti
    })

def add_folder(request):

    if request.method == 'POST':
        user = User.objects.get(user_id=request.session.get('user_id'))  

        folder_name = request.POST['folder_name']
        
        if Folder.objects.filter(user=user, folder_name=folder_name).exists():
            messages.error(request,"A folder with this name already exists.")
            return redirect('folder') 
        else:

            newFolder = Folder.objects.create(
                user=user,
                folder_name=folder_name
            )
            
            newFolder.save()

    return redirect('folder')

def edit_folder(request,folder_id):

    if request.method == 'POST':
        action = request.POST.get('action')
        user = User.objects.get(user_id=request.session.get('user_id'))  
        actionFolder = Folder.objects.get(user=user,folder_id=folder_id)

        if action == 'edit':

            actionFolder_name = request.POST['folder_name']
            if Folder.objects.filter(user=user,folder_name=actionFolder_name).exists():
                messages.error(request,"A folder with this name already exists.")
                return redirect('folder')
            
            actionFolder.folder_name = actionFolder_name
                    
            actionFolder.save()

        elif action == 'delete':

            actionFolder.delete()

    folders = Folder.objects.filter(user=user)

    return render(request,'folder.html',{'user':user,'folders':folders})

def add_word(request,folder_id):
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user = User.objects.get(user_id=request.session.get('user_id')) 
        folder = Folder.objects.get(user=user,folder_id=folder_id)

        word = request.POST['word_name']

        if Word.objects.filter(user=user, folder=folder,word=word).exists():
                messages.error(request,"Word with this name already exists.")
                return word_view(request,folder_id)

        if action == 'add':
            meaning = request.POST['meaning']
            newWord = Word.objects.create(
                user = user,
                folder = folder,
                word = word,
                meaning = meaning
            )
            newWord.save()
    
    # words = Word.objects.filter(user=user,folder=folder)
    return word_view(request,folder_id)

def upload_flashcards(request, folder_id):
    """
    ฟังก์ชันสำหรับอัปโหลดไฟล์ Flashcards (ในรูปแบบ CSV หรือ Excel)
    """
    if request.method == 'POST':
        try:
            # ตรวจสอบ user จาก session
            user = User.objects.get(user_id=request.session.get('user_id'))
        except User.DoesNotExist:
            messages.error(request, "User not found. Please login.")
            return redirect('login')

        try:
            # ตรวจสอบโฟลเดอร์
            folder = Folder.objects.get(user=user, folder_id=folder_id)
        except Folder.DoesNotExist:
            messages.error(request, "Folder not found.")
            return word_view(request,folder_id)

        # ตรวจสอบว่าไฟล์ถูกส่งมาหรือไม่
        if 'flashcards_file' not in request.FILES:
            messages.error(request, "No file uploaded.")
            return word_view(request, folder_id)

        # อ่านไฟล์
        flashcards_file = request.FILES['flashcards_file']
        file_extension = flashcards_file.name.split('.')[-1].lower()

        try:
            '''# อ่านไฟล์ CSV หรือ Excel ขึ้นอยู่กับชนิดไฟล์
            if file_extension == 'csv':
                #decoded_file = flashcards_file.read().decode('ISO-8859-1').splitlines()
                flashcards_file.seek(0)  # รีเซ็ต pointer
                decoded_file = codecs.decode(flashcards_file.read(), 'tis-620').splitlines()
                reader = pd.read_csv(io.StringIO('\n'.join(decoded_file)))
            elif file_extension in ['xls', 'xlsx']:
                # ใช้ pandas อ่านไฟล์ Excel
                reader = pd.read_excel(flashcards_file)
            else:
                messages.warning(request, "Unsupported file format. Please upload a CSV or Excel file.")
                return word_view(request, folder_id)'''
            # อ่านไฟล์และใช้ chardet ตรวจสอบ encoding
            raw_data = flashcards_file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']  # ค่า encoding ที่ chardet ตรวจพบ
            print(f"Detected encoding: {encoding}")  # ตรวจสอบ encoding ที่ถูกตรวจพบ

            flashcards_file.seek(0)  # รีเซ็ต pointer ของไฟล์

            # อ่านไฟล์ด้วย encoding ที่ตรวจพบ
            if file_extension == 'csv':
                # ใช้ open() สำหรับอ่านไฟล์
                data = flashcards_file.read().decode(encoding, errors='ignore')
                # ส่งข้อมูลไปให้ pandas อ่าน
                from io import StringIO
                reader = pd.read_csv(StringIO(data))
            elif file_extension in ['xls', 'xlsx']:
                reader = pd.read_excel(io.BytesIO(flashcards_file.read()))
            else:
                messages.warning(request, "Unsupported file format. Please upload a CSV or Excel file.")
                return word_view(request, folder_id)
            
            #เก็บคำศัพท์จากไฟล์ที่อัปโหลด
            words_data = []
            for index, row in reader.iterrows():
                if len(row) != 2:
                    # ตรวจสอบว่าไฟล์มีสองคอลัมน์หรือไม่
                    messages.warning(request, "Invalid format in file. Each row must contain a word and a meaning.")
                    continue
                
                #word, meaning = row[0], row[1]
                word, meaning = row.iloc[0], row.iloc[1]
                word = word.strip()
                meaning = meaning.strip()
                
                # แก้ไขการแสดงผลของข้อความที่มีการเข้ารหัสเป็น Unicode
                #meaning = bytes(meaning, 'utf-8').decode('tis-620')

                # ตรวจสอบว่าคำศัพท์ซ้ำหรือไม่
                if Word.objects.filter(user=user, folder=folder, word=word).exists():
                    messages.warning(request, f"Word '{word}' already exists. Skipping.")
                    continue

                # สร้างคำศัพท์ใหม่
                new_word = Word.objects.create(
                    user=user,
                    folder=folder,
                    word=word,
                    meaning=meaning
                )
                new_word.save()
                words_data.append({'word': word, 'meaning': meaning})

            # ส่งข้อมูลคำศัพท์กลับไปยังหน้าจอ
            #return JsonResponse({'success': True, 'words': words_data})
            return word_view(request,folder_id)

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            #return JsonResponse({'success': False, 'error': str(e)})

    return word_view(request,folder_id)

def edit_word(request,folder_id,word_id):
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user = User.objects.get(user_id=request.session.get('user_id'))  
        folder = Folder.objects.get(user=user,folder_id=folder_id)

        if action == 'edit':
            word = request.POST['word_name']
            meaning = request.POST['meaning']
            
            if Word.objects.filter(user=user, folder=folder,word=word,meaning=meaning).exists():
                messages.error(request,"Word with this name already exists.")
                return word_view(request,folder_id)

            editWord = Word.objects.get(user=user,folder=folder,word_id=word_id)

            editWord.word = word
            editWord.meaning = meaning
                
            editWord.save()
        elif action == 'delete':

            deleteWord = Word.objects.get(user=user,folder=folder,word_id=word_id)

            deleteWord.delete()
            Word.reorder_word_ids(deleteWord.user, deleteWord.folder)

    words = Word.objects.filter(user=user,folder=folder)

    return render(request,'word.html',{'words' : words,'folder':folder})

def search_folder(request):
    query = request.GET.get('query', '')
    user = User.objects.get(user_id=request.session.get('user_id'))

    if not query:
        return folder_view(request) 
    else:
        search_results = Folder.objects.filter(folder_name__icontains=query, user=user)

    if search_results:
        return render(request, 'folder.html', {'user': user, 'folders': search_results})
    else:
        error_message = "No folders found matching " + query + ". Try another search term."
        return render(request, 'folder.html', {'user': user, 'folders': search_results, 'noti': error_message})
    
def search_word(request,folder_id):
    query = request.GET.get('query', '')
    user = User.objects.get(user_id=request.session.get('user_id'))
    folder = Folder.objects.get(user=user,folder_id=folder_id)

    if not query:
        return word_view(request,folder_id) 
    else:
        search_results = Word.objects.filter(word__icontains=query, user=user,folder=folder)

    if search_results:
        return render(request, 'word.html', {'user': user, 'folder': folder, 'words' : search_results})
    else:
        error_message = "No words found matching " + query + ". Try another search term."
        return render(request, 'word.html', {'user': user, 'folder': folder, 'words' : search_results, 'noti':error_message})

def select_game_view(request,folder_id):
    return render(request, 'selGame.html',{'folder_id':folder_id})

# ฟังก์ชันใหม่สำหรับแสดงหน้า timeSet.html
def time_set_view(request,folder_id):
    return render(request, 'timeSet.html',{'folder_id':folder_id})

# ฟังก์ชันใหม่สำหรับแสดงหน้า modeSet.html
def mode_set_view(request,folder_id):
    return render(request, 'wordGuessMode.html',{'folder_id':folder_id})

def score(request):
    user = User.objects.get(user_id=request.session.get('user_id'))
    noti = None
    query = request.GET.get('query', None)

    game_1_scores = Highscore.objects.filter(user=user, game_id=1)
    game_2_scores = Highscore.objects.filter(user=user, game_id=2)
    game_3_scores = Highscore.objects.filter(user=user, game_id=3)

    if query:
        folders = Folder.objects.filter(user=user, folder_name__icontains=query)  # กรองตาม query

        if not folders:
            folders = Folder.objects.filter(user=user)
            noti = "No scores found matching " + query + ". Try another search term."
        
    else:
        folders = Folder.objects.filter(user=user)
        if not folders:
            return render(request, 'score.html',{'user': user})

    fig, axs = plt.subplots(len(folders), 3, figsize=(15, len(folders) * 5))

    # ถ้ามีแค่ 1 folder ก็จะเป็นแค่ 1 แถว
    if len(folders) == 1:
        axs = [axs]

    for i, folder in enumerate(folders):
        # กรองข้อมูลของแต่ละ folder สำหรับเกมแต่ละเกม
        folder_game_1_scores = game_1_scores.filter(folder=folder)[:20]  # กรองตาม folder และจำกัดจำนวน
        folder_game_2_scores = game_2_scores.filter(folder=folder)[:20]
        folder_game_3_scores = game_3_scores.filter(folder=folder)[:20]

        # สร้างกราฟสำหรับเกม 1
        folder_game_1_play_times = [score.play_time for score in folder_game_1_scores]
        folder_game_1_scores_values = [score.score for score in folder_game_1_scores]
        axs[i][0].plot(folder_game_1_play_times, folder_game_1_scores_values, marker='o', linestyle='-', color='b')
        axs[i][0].set(xlabel='Play Time', ylabel='Score', title=f'Game Flashcard: Folder {folder.folder_name}')
        axs[i][0].xaxis.set_major_locator(MaxNLocator(integer=True))  # แสดงค่าจำนวนเต็มบนแกน x
        axs[i][0].yaxis.set_major_locator(MaxNLocator(integer=True))  # แสดงค่าจำนวนเต็มบนแกน y
        axs[i][0].grid(False)

        # สร้างกราฟสำหรับเกม 2
        folder_game_2_play_times = [score.play_time for score in folder_game_2_scores]
        folder_game_2_scores_values = [score.score for score in folder_game_2_scores]
        axs[i][1].plot(folder_game_2_play_times, folder_game_2_scores_values, marker='o', linestyle='-', color='g')
        axs[i][1].set(xlabel='Play Time', ylabel='Score', title=f'Game Wordguess: Folder {folder.folder_name}')
        axs[i][1].xaxis.set_major_locator(MaxNLocator(integer=True))  # แสดงค่าจำนวนเต็มบนแกน x
        axs[i][1].yaxis.set_major_locator(MaxNLocator(integer=True))  # แสดงค่าจำนวนเต็มบนแกน y
        axs[i][1].grid(False)

        # สร้างกราฟสำหรับเกม 3
        folder_game_3_play_times = [score.play_time for score in folder_game_3_scores]
        folder_game_3_scores_values = [score.score for score in folder_game_3_scores]
        axs[i][2].plot(folder_game_3_play_times, folder_game_3_scores_values, marker='o', linestyle='-', color='r')
        axs[i][2].set(xlabel='Play Time', ylabel='Score', title=f'Game Flashcard multiple choice: Folder {folder.folder_name}')
        axs[i][2].xaxis.set_major_locator(MaxNLocator(integer=True))  # แสดงค่าจำนวนเต็มบนแกน x
        axs[i][2].yaxis.set_major_locator(MaxNLocator(integer=True))  # แสดงค่าจำนวนเต็มบนแกน y
        axs[i][2].grid(False)

    # ปรับแต่งการจัด layout เพื่อให้กราฟไม่ทับซ้อน
    plt.tight_layout(pad=2.0)  # เพิ่มช่องว่างระหว่างกราฟ

    # บันทึกกราฟลงใน buffer
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # แปลงกราฟเป็น base64
    graph_data = base64.b64encode(buf.getvalue()).decode('utf-8')

    # ส่งข้อมูลกราฟไปยัง template
    return render(request, 'score.html', {
        'user': user,
        'graph': graph_data,
        'folders': folders,
        'noti' : noti  # ส่งข้อมูล folder ไปยัง template
    })

def check_in(request):
    user = User.objects.get(user_id=request.session.get('user_id'))
    user.check_in()
    return redirect('folder')

def reward(request):
    user = User.objects.get(user_id=request.session.get('user_id'))
    return render(request,'reward.html',{'user':user})

def redeem_reward(request,reward_id):
    user = User.objects.get(user_id=request.session.get('user_id'))

    title_available = ['Letter Seeker','Word Explorer','Rookie Linguist','Sentence Spinner','Riddle Solver','Master of Meaning','Word Wizard','Word God','Linguistic Overlord']
    title_costs = [10, 20, 50, 80, 100, 150, 200, 300, 500]

    card_color_available = ['#FF5733','#5BC0EB','#28A745','#FFC107','#D1A1D3','#F06292','linear-gradient(45deg, #F06292, #9C27B0)','linear-gradient(45deg, #5BC0EB, #28A745)','linear-gradient(45deg, #FFC107, #FF7043)']
    card_color_costs = [100,100,100,100,100,100,300,300,300]

    colors = [
        "#D3D3D3", "#F0F0F0", "#8B8B8B", "#B0B0B0", "#A9A9A9", 
        "#FF8C00", "#FF6347", "#FFD700", "#87CEFA", "#98FB98",
        "#FF69B4", "#00BFFF", "#32CD32", "#FF4500", "#9932CC",
        "#FF1493", "#8A2BE2", "#7FFF00", "#FF6347", "#00CED1"
    ]
    
    gradients = [
        "linear-gradient(45deg, #D3D3D3, #F0F0F0)", "linear-gradient(45deg, #FF8C00, #FF6347)",
        "linear-gradient(45deg, #FFD700, #98FB98)", "linear-gradient(45deg, #87CEFA, #FFD700)",
        "linear-gradient(45deg, #FF69B4, #FF4500)", "linear-gradient(45deg, #00BFFF, #32CD32)",
        "linear-gradient(45deg, #9932CC, #FF69B4)", "linear-gradient(45deg, #FF4500, #00BFFF)"
    ]
    
    lucky_chest = colors + gradients
    weights = [3] * len(colors) + [1] * len(gradients)

    message = 'Redeem Success!'

    title_ava = user.get_title_ava()  # แปลง JSON string เป็น list
    card_color_ava = user.get_card_color_ava()  # แปลง JSON string เป็น list

    if(reward_id == 0):
        user.credits += 10
        user.day_streak_left -= 3

    elif(reward_id == 999):
        user.hint_ava += 1
        user.credits -= 50

    elif reward_id >= 1 and reward_id <= 9:
        title = title_available[reward_id - 1]
        cost = title_costs[reward_id - 1]

        if title not in title_ava:
            title_ava.append(title)  # เพิ่ม title ที่ได้จาก reward_id

        user.credits -= cost

    elif reward_id >= 10 and reward_id <= 18:
        card_color = card_color_available[reward_id - 10]
        cost = card_color_costs[reward_id - 10]

        if card_color not in card_color_ava:
            card_color_ava.append(card_color)
        
        user.credits -= cost

    elif(reward_id == 50):
        card_color = random.choices(lucky_chest, weights=weights, k=1)[0]
        if card_color not in card_color_ava:
            message = f'You have got {card_color}. Congratulations! A new card color has been added.'
            card_color_ava.append(card_color)
        else:
            message = f'You have got {card_color}. You already have this color.'
        
        user.credits -= 150

    else:
        error_message = 'Invalid reward_id!'
        return render(request,'reward.html',{'user':user,'noti':error_message}) 
    
    user.save()
    return render(request,'reward.html',{'user':user,'noti':message}) 

def community(request):
    user = User.objects.get(user_id=request.session.get('user_id'))
    folders = Folder.objects.filter(user=user)
    top_users = User.objects.order_by('-day_streak')[:10]
    top_users = list(top_users) + ['-'] * (10 - len(top_users)) 
    open_games = PublicGame.objects.filter(status='OPEN')

    for game in open_games:
        game.is_joined = game.players.filter(user=user).exists()

    return render(request, 'community.html', {
        'user': user,
        'top_users': top_users,
        'folders': folders,
        'open_games':open_games
    })

def add_public_game(request):
    if request.method == 'POST':
        creator = User.objects.get(user_id=request.session.get('user_id'))
        name = request.POST.get('name')
        description = request.POST.get('description')
        max_players = request.POST.get('max_players')
        folder_id = request.POST.get('folder')
        game_type = request.POST.get('game_type')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        status = request.POST.get('status')

        # Get the folder object from the id
        folder = Folder.objects.get(id=folder_id)

        # Create the new game
        game = PublicGame(
            creator = creator,
            name=name,
            description=description,
            max_players=max_players,
            folder=folder,
            game_type=game_type,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )
        game.save()

        # Redirect to a success page or the same page with a success message
        return redirect('community')  # Replace with your desired redirect view

    else:
        # If the method is GET, pass the folders of the logged-in user
        folders = Folder.objects.filter(user=request.session.get('user_id'))
        return render(request, 'folder.html', {'folders': folders})
    
def join_game(request, game_id):
    user = User.objects.get(user_id=request.session.get('user_id'))
    game = PublicGame.objects.get(id=game_id)

    if not game.players.filter(user=user).exists():
        GamePlayer.objects.create(game=game, user=user)

    # Get the game type and difficulty
    game_type = game.game_type
    request.session['user_id_admin'] = game.creator.user_id
    request.session['folder_id_admin'] = game.folder.folder_id
    # Redirect based on the game type
    if game_type == 'FLASHCARD':
        return redirect('flashcard', folder_id=game.folder.folder_id)
    elif game_type == 'FLASHCARDCHOICE':
        return redirect('flashcard_choice', folder_id=game.folder.folder_id)
    elif game_type == 'WORDGUESS_EASY':
        url = reverse('wordguess', kwargs={'folder_id': game.folder.folder_id})
        return redirect(f'{url}?difficulty=easy')
    elif game_type == 'WORDGUESS_NORMAL':
        url = reverse('wordguess', kwargs={'folder_id': game.folder.folder_id})
        return redirect(f'{url}?difficulty=normal')
    elif game_type == 'WORDGUESS_HARD':
        url = reverse('wordguess', kwargs={'folder_id': game.folder.folder_id})
        return redirect(f'{url}?difficulty=hard')

    return redirect('community') 