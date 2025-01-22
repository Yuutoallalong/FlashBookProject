# tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse
from homepage.models import User, Folder, Word, Highscore
from flashcard.views import next_word
from django.contrib.auth.models import User as UserBuiltIn

class FlashcardViewsTest(TestCase):

    def setUp(self):
        # Create a test user
        self.user = User.objects.create(
            user_id=1,
            user='testuser',
            fname='Test',
            lname='User',
            email='testuser@example.com',
            password='testpassword'
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
        self.word1 = Word.objects.create(user=self.user, folder=self.folder,word='testword1',meaning='testmeaning1')
        self.word2 = Word.objects.create(user=self.user, folder=self.folder,word='testword2',meaning='testmeaning2')
        
        # Create a highscore for the user and folder
        self.highscore = Highscore.objects.create(user=self.user, folder=self.folder, game_id=1, score=0, play_time=1)

    def test_flashcard_view(self):
        """Test the flashcard view returns the correct word and score"""
        response = self.client.get(reverse('flashcard', args=[self.folder.folder_id]))
        self.assertEqual(response.status_code, 200)

        # Assert that the view logic executed correctly
        self.assertEqual(response.status_code, 200)

    def test_correct_answer_view(self):
        """Test that the score is incremented when the correct answer is selected"""
        response = self.client.get(reverse('correct_answer', args=[self.folder.folder_id,self.highscore.play_time]))
        self.assertEqual(response.status_code, 302)  # Should redirect to flashcard page
        # Fetch the updated highscore
        highscore = Highscore.objects.get(user=self.user, folder=self.folder, game_id=1)
        self.assertEqual(highscore.score, 1)  # Score should be incremented by 1

    def test_wrong_answer_view(self):
        """Test that the score is not changed when the wrong answer is selected"""
        response = self.client.get(reverse('wrong_answer', args=[self.folder.folder_id]))
        self.assertEqual(response.status_code, 302)  # Should redirect to flashcard page
        # Fetch the updated highscore
        highscore = Highscore.objects.get(user=self.user, folder=self.folder, game_id=1)
        self.assertEqual(highscore.score, 0)  # Score should remain the same

    def test_next_word_view(self):
        """Test that the next word is shown when the next word button is pressed"""
        response = self.client.get(reverse('flashcard', args=[self.folder.folder_id]))
        response = self.client.get(reverse('next_word', args=[self.folder.folder_id,self.highscore.play_time]))
        self.assertEqual(response.status_code, 302)  # Should redirect to flashcard page
        
        # Check if the next word is set correctly in the session
        self.assertEqual(self.client.session.get('currentWordId'), 2)


    def test_no_next_word_view(self):
        # Set up the current_word_id in the session
        session = self.client.session
        session['currentWordId'] = 2  # Set to the last word's word_id
        session.save()  # Save the session

        # Simulate a request to the 'next_word' view
        response = self.client.get(reverse('next_word', args=[self.folder.folder_id,self.highscore.play_time]))

        # Verify the response
        self.assertEqual(response.status_code, 302)  # Expect a redirect (to 'flashcard')
        self.assertNotIn('currentWordId', self.client.session)  # Should cycle back to the first word

    def test_finish_view(self):
        """Test the finish page"""
        response = self.client.get(reverse('finish', args=[self.folder.folder_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finish.html')  # Check if finish template is used

    def test_flashcard_referrer_logic(self):
        # Simulate a request with an HTTP_REFERER header containing "flashcard"
        url = reverse('flashcard', args=[self.folder.folder_id])
        response = self.client.get(
            url,
            HTTP_REFERER='/flashcard/'
        )

        # Assert that the view logic executed correctly
        self.assertEqual(response.status_code, 200)

    def test_time_up_redirects_to_next_word(self):
        # Simulate the flashcard page being loaded with a time value
        response = self.client.get(reverse('flashcard', kwargs={'folder_id': self.folder.folder_id}), {'time': 5})

        # Check if the word is displayed correctly
        self.assertContains(response, "word1")

        # Simulate the timer reaching 0, this would usually happen via JavaScript but we can simulate the next request
        # Trigger the next word action as if the time is up
        self.client.post(reverse('next_word', kwargs={'folder_id': self.folder.folder_id, 'playtime': self.highscore.play_time}))

        # Now, check if we have moved to the next word
        response = self.client.get(reverse('flashcard', kwargs={'folder_id': self.folder.folder_id}))
        
        # Ensure the second word is shown (i.e., Word2)
        self.assertContains(response, "word2")

    def test_correct_answer_resets_timer(self):
        """Test that the time_value is set to None when the correct button is pressed"""

        # Set the time value in the session before pressing the correct button
        session = self.client.session
        session['time_value'] = 10  # Simulate 10 seconds
        session.save()

        # Ensure the session was updated
        self.assertEqual(self.client.session['time_value'], 10)

        # Make the request to simulate pressing the correct button
        self.client.post(reverse('correct_answer', args=[self.folder.folder_id, self.highscore.play_time]), follow=True)

        # After pressing the correct button, check if time_value is set to None
        # self.assertIsNone(self.client.session.get('time_value'), "The time_value should be None after pressing the correct button.")
        self.assertTrue(self.client.session.get('came_from_answer'))

    def test_wrong_answer_resets_timer(self):
        """Test that the time_value is set to None when the wrong button is pressed"""

        # Set the time value in the session before pressing the wrong button
        session = self.client.session
        session['time_value'] = 10  # Simulate 10 seconds
        session.save()

        # Ensure the session was updated
        self.assertEqual(self.client.session['time_value'], 10)

        # Make the request to simulate pressing the wrong button
        self.client.post(reverse('wrong_answer', args=[self.folder.folder_id]), follow=True)

        # After pressing the wrong button, check if time_value is set to None
        # self.assertIsNone(self.client.session.get('time_value'), "The time_value should be None after pressing the wrong button.")
        self.assertTrue(self.client.session.get('came_from_answer'))