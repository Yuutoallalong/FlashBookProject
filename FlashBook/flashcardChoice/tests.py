from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User as DjangoUser
from homepage.models import User, Folder, Word, Highscore
from django.test import Client
import random

class FlashcardChoiceViewsTest(TestCase):

    def setUp(self):
        # Set up a user, folder, words, and highscore for the tests
        self.client = Client()

        # Create a Django user and login
        self.django_user = DjangoUser.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        # Create a custom User object for the app
        self.user = User.objects.create(user='testuser', fname='Test', lname='User', email='testuser@example.com')

        # Create a Folder for the user
        self.folder = Folder.objects.create(user=self.user, folder_id=1, folder_name='Test Folder')

        # Create multiple words for the flashcard game
        self.word_1 = Word.objects.create(user=self.user, folder=self.folder, word_id=1, word='apple', meaning='a fruit')
        self.word_2 = Word.objects.create(user=self.user, folder=self.folder, word_id=2, word='banana', meaning='another fruit')
        self.word_3 = Word.objects.create(user=self.user, folder=self.folder, word_id=3, word='cat', meaning='a small domesticated carnivorous mammal')
        self.word_4 = Word.objects.create(user=self.user, folder=self.folder, word_id=4, word='dog', meaning='a domesticated carnivorous mammal')
        self.word_5 = Word.objects.create(user=self.user, folder=self.folder, word_id=5, word='elephant', meaning='a large mammal with a trunk')

        # Create a Highscore entry for the game
        self.highscore = Highscore.objects.create(user=self.user, folder=self.folder, game_id=3, play_time=1, score=0)

    def test_flashcard_choice_view(self):
        # Test that the 'flashcard_choice' view renders correctly with necessary context
        url = reverse('flashcard_choice', kwargs={'folder_id': self.folder.folder_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'flashcardChoice.html')
        self.assertIn('highscore', response.context)
        self.assertIn('user', response.context)
        self.assertIn('word', response.context)
        self.assertIn('folder', response.context)
        self.assertIn('answers', response.context)
        self.assertIn('pop_up_message_correct', response.context)

    def test_check_answer_correct(self):
        # Test submitting a correct answer increases the score and redirects back to flashcard_choice
        url = reverse('check_answer', kwargs={'folder_id': self.folder.folder_id, 'play_time': self.highscore.play_time})
        response = self.client.post(url, {'selected_answer': 'a fruit', 'correct_answer': 'a fruit'})
        self.assertRedirects(response, reverse('flashcard_choice', kwargs={'folder_id': self.folder.folder_id}))
        self.highscore.refresh_from_db()
        self.assertEqual(self.highscore.score, 1)

    def test_check_answer_incorrect(self):
        # Test submitting an incorrect answer keeps the score unchanged and redirects back to flashcard_choice
        url = reverse('check_answer', kwargs={'folder_id': self.folder.folder_id, 'play_time': self.highscore.play_time})
        response = self.client.post(url, {'selected_answer': 'another fruit', 'correct_answer': 'a fruit'})
        self.assertRedirects(response, reverse('flashcard_choice', kwargs={'folder_id': self.folder.folder_id}))
        self.highscore.refresh_from_db()
        self.assertEqual(self.highscore.score, 0)

    def test_finish_choice_view(self):
        # Set up the session variable
        session = self.client.session
        session['pop_up_message_correct'] = "Test message"
        session.save()

        # Make the request
        url = reverse('finish_choice', kwargs={'folder_id': self.folder.folder_id})
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finishChoice.html')
        self.assertIn('highscore', response.context)
        self.assertIn('pop_up_message_correct', response.context)
        self.assertEqual(response.context['pop_up_message_correct'], "Test message")

    def test_redirect_to_finish_choice(self):
        # Simulate the session at the last word
        session = self.client.session
        session['currentWordId'] = self.word_5.word_id
        session['is_first_visit'] = False
        session.save()

        # Make a GET request to the flashcard_choice view
        response = self.client.get(reverse('flashcard_choice', args=[self.folder.folder_id]))

        # Verify the session variables are cleared
        session = self.client.session
        self.assertNotIn('currentWordId', session)
        self.assertNotIn('is_first_visit', session)

        # Verify the response redirects to the finish_choice view
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('finish_choice', args=[self.folder.folder_id]))

    def test_flashcard_choice_first_and_subsequent_visits(self):
        # Simulate the first visit
        self.client.session['is_first_visit'] = True
        url = reverse('flashcard_choice', kwargs={'folder_id': self.folder.folder_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('answers', response.context)

        # Simulate a subsequent visit with a next word
        self.client.session['currentWordId'] = self.word_1.word_id
        self.client.session['is_first_visit'] = False
        url = reverse('flashcard_choice', kwargs={'folder_id': self.folder.folder_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('answers', response.context)
        self.assertEqual(self.client.session['currentWordId'], self.word_2.word_id)  # Ensure it progresses to the next word


    def test_flashcard_choice_referrer_logic(self):
        # Simulate a request with an HTTP_REFERER header containing "flashcard_choice"
        url = reverse('flashcard_choice', args=[self.folder.folder_id])
        response = self.client.get(
            url,
            HTTP_REFERER='/flashcardChoice/'
        )

        # Assert that the view logic executed correctly
        self.assertEqual(response.status_code, 200)

    def test_time_value_passed_to_view(self):
        # Test that time value can be passed and stored correctly
        url = reverse('flashcard_choice', kwargs={'folder_id': self.folder.folder_id})
        response = self.client.get(url, {'time': '60'})
        
        # Check that the time value is in the context and session
        self.assertEqual(response.context['time_value'], '60')
        self.assertEqual(self.client.session['time_value'], '60')
        self.assertEqual(response.status_code, 200)

    def test_time_value_persistence_across_requests(self):
        # Test that time value persists across multiple requests
        # First request with time value
        url = reverse('flashcard_choice', kwargs={'folder_id': self.folder.folder_id})
        self.client.get(url, {'time': '90'})
        
        # Second request without time value should use previous session value
        response = self.client.get(url)
        
        # Check that the previous time value is used
        self.assertEqual(response.context['time_value'], '90')
        self.assertEqual(self.client.session['time_value'], '90')
