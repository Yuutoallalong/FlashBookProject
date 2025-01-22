from django.test import TestCase, Client
from homepage.models import User, Folder, Word, Highscore
from django.contrib.auth.models import User as UserBuiltIn
from django.urls import reverse


class WordGuessViewTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create(
            user_id=1,
            user='testuser',
            fname='Test',
            lname='User',
            email='testuser@example.com',
            password='testpassword',
            hint_ava=1
        )

        self.user_built_in = UserBuiltIn.objects.create_user(
            username='testuser',
            password='testpassword',
            first_name='Test',
            last_name='User',
            email='testuser@example.com'
        )

        self.client = Client()
        
        login_url = reverse('login')
        response = self.client.get(login_url)
        csrf_token = response.cookies['csrftoken'].value

        response = self.client.post(
            login_url,
            {   
                'csrfmiddlewaretoken': csrf_token,
                'username': 'testuser',
                'password': 'testpassword'
            }
        )

        # Create a folder for the user
        self.folder = Folder.objects.create(user=self.user, folder_name='Folder1')
        
        # Create some words for the flashcards
        self.word1 = Word.objects.create(user=self.user, folder=self.folder,word='TESTWORD1',meaning='testmeaning1')
        self.word2 = Word.objects.create(user=self.user, folder=self.folder,word='TESTword2',meaning='testmeaning2')
        self.word2 = Word.objects.create(user=self.user, folder=self.folder,word='testword3',meaning='testmeaning3')
        
        # Create a highscore for the user and folder
        self.highscore = Highscore.objects.create(user=self.user, folder=self.folder, game_id=2, score=0, play_time=1)

    def test_wordguess_referrer_logic(self):
        # Simulate a request with an HTTP_REFERER header containing "flashcard"
        url = reverse('wordguess', args=[self.folder.folder_id])
        response = self.client.get(
            url,
            HTTP_REFERER='/wordguess/'
        )

        # Assert that the view logic executed correctly
        self.assertEqual(response.status_code, 200)

    def test_initial_easy_mode(self):
        response = self.client.get(reverse('wordguess', args=[self.folder.folder_id]), {'difficulty': 'easy'})
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        word = response.context.get('word')
        guesses = session['guesses']
        self.assertGreaterEqual(len(guesses), len(word.word) // 2)
        self.assertEqual(session['hearts_left'], 6)

    def test_initial_normal_mode(self):
        response = self.client.get(reverse('wordguess', args=[self.folder.folder_id]), {'difficulty': 'normal'})
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        word = response.context.get('word')
        guesses = session['guesses']
        self.assertGreaterEqual(len(guesses), len(word.word) // 4)
        self.assertEqual(session['hearts_left'], 6)

    def test_initial_hard_mode(self):
        response = self.client.get(reverse('wordguess', args=[self.folder.folder_id]), {'difficulty': 'hard'})
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertEqual(len(session['guesses']), 0)
        self.assertEqual(session['hearts_left'], 4)

    def test_correct_guess(self):
        response = self.client.get(reverse('wordguess', args=[self.folder.folder_id]))
        session = self.client.session
        word = response.context.get('word')
        correct_letter = word.word[0].lower()

        response = self.client.post(reverse('wordguess', args=[self.folder.folder_id]), {'guess': correct_letter})
        session = self.client.session
        self.assertEqual(response.status_code, 200)
        self.assertIn(correct_letter, session['guesses'])
        self.assertEqual(session['hearts_left'], 6)

    def test_incorrect_guess(self):
        response = self.client.get(reverse('wordguess', args=[self.folder.folder_id]))
        session = self.client.session
        word = response.context.get('word')
        incorrect_letter = 'z'
        while incorrect_letter in word.word.lower():
            incorrect_letter = chr(ord(incorrect_letter) + 1)

        response = self.client.post(reverse('wordguess', args=[self.folder.folder_id]), {'guess': incorrect_letter})
        session = self.client.session
        self.assertEqual(response.status_code, 200)
        self.assertIn(incorrect_letter, session['guesses'])
        self.assertEqual(session['hearts_left'], 5)

    def test_game_end_success(self):
        response = self.client.get(reverse('wordguess', args=[self.folder.folder_id]), {'difficulty': 'normal'})
        session = self.client.session
    
        forced_guesses = ['t','e','s','t','w','o','r','d','1','2','3']
        
        for guess in forced_guesses:
            response = self.client.post(reverse('wordguess', args=[self.folder.folder_id]), {'guess': guess})
            session = self.client.session
            if session.get('game_end') == True:

                break
        
        
        session = self.client.session
        highscore = response.context.get('highscore')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(session.get('word_id'))
        self.assertIn("Congratulations! You guessed the word!", response.context.get('message'))
        self.assertEqual(highscore.score, 1)

    def test_game_end_failure(self):
        response = self.client.get(reverse('wordguess', args=[self.folder.folder_id]), {'difficulty': 'normal'})
        session = self.client.session
        
        forced_guesses = ['a','b','c','f','g','h']

        for guess in forced_guesses:
            response = self.client.post(reverse('wordguess', args=[self.folder.folder_id]), {'guess': guess})
            session = self.client.session
            if session.get('game_end') == True:
                break
        
        self.highscore.refresh_from_db()
        session = self.client.session
        highscore = response.context.get('highscore')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(session.get('word_id'))
        self.assertIn("You lost!", response.context.get('message'))
        self.assertEqual(highscore.score, 0)

    def test_hint_available(self):
        response = self.client.post(reverse('wordguess', args=[self.folder.folder_id]), {'hint_request': 'true'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.hint_ava, 0)
        hint_message = response.context.get('hint_message')
        self.assertIsNotNone(hint_message)

    def test_hint_not_available(self):
        self.user.hint_ava = 0
        self.user.save()
        response = self.client.post(reverse('wordguess', args=[self.folder.folder_id]), {'hint_request': 'true'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.hint_ava, 0)
        hint_message = response.context.get('hint_message')
        self.assertEqual(hint_message,"Not enough hint!")
