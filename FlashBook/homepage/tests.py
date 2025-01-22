from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from .forms import RegisterForm, LoginForm
from django.contrib.messages import get_messages
from .models import User as User_model
from .models import Folder, Word, Highscore
from homepage.models import User as CustomUser
from homepage.views import homepage, about, register, login_views, logout_views, profile_view
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User as AuthUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.utils import IntegrityError
from django.test import TestCase, TransactionTestCase
import os

class RegisterLoginTests(TransactionTestCase):
    # ใช้ TransactionTestCase แทน TestCase
    reset_sequences = True

    # เตรียมข้อมูลสำหรับทดสอบ
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.homepage_url = reverse('homepage')
        self.about_url = reverse('about')
        self.admin_url = '/admin/'
        self.user_credentials = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        self.admin_credentials = {
            'username': 'adminuser',
            'password': 'adminpassword123',
            'is_staff': True
        }
        self.user = User.objects.create_user(**self.user_credentials)
        self.admin_user = User.objects.create_user(**self.admin_credentials)

        self.user_model = User_model.objects.create(
            user_id=1,
            user='testuser',
            fname='Test',
            lname='User',
            email='testuser@example.com',
            password='testpassword123'
        )

    # ทดสอบหน้า homepage เพื่อให้แน่ใจว่าสามารถโหลดได้สำเร็จและใช้ template ที่ถูกต้อง
    def test_homepage_view(self):
        response = self.client.get(self.homepage_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage.html')

    # ทดสอบหน้า about เพื่อให้แน่ใจว่าสามารถโหลดได้สำเร็จและใช้ template ที่ถูกต้อง
    def test_about_view(self):
        response = self.client.get(self.about_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')

    # ทดสอบหน้า register ด้วยการส่ง GET request เพื่อให้แน่ใจว่าแบบฟอร์มการลงทะเบียนโหลดได้สำเร็จ
    def test_register_view_get(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertIsInstance(response.context['form'], RegisterForm)

    # ทดสอบหน้า register ด้วยการส่งข้อมูล POST ที่ถูกต้อง (happy path)
    def test_register_view_post_valid(self):
        valid_data = {
            'username': 'newuser',
            'fname': 'New',
            'lname': 'User',
            'email': 'newuser@example.com',
            'birthdate': '2000-01-01',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        }
        response = self.client.post(self.register_url, data=valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    # ทดสอบหน้า register ด้วยการส่งข้อมูล POST ที่ไม่ถูกต้อง (sad path)
    def test_register_view_post_invalid(self):
        invalid_data = {
            'username': '',  # Username จำเป็นแต่ไม่มีการกรอกข้อมูล
            'fname': 'New',
            'lname': 'User',
            'email': 'invalidemail',  # รูปแบบอีเมลไม่ถูกต้อง
            'birthdate': '2000-01-01',
            'password1': 'newpassword123',
            'password2': 'differentpassword'  # รหัสผ่านไม่ตรงกัน
        }
        response = self.client.post(self.register_url, data=invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertFalse(User.objects.filter(username='').exists())

        # ทดสอบหน้า register ด้วยการส่งข้อมูล POST ที่ทำให้เกิด email ซ้ำ (unique constraint)
    def test_register_view_post_duplicate_email(self):
        # สร้างข้อมูลซ้ำก่อน
        User.objects.create_user(username='existinguser', password='somepassword123', email='duplicate@example.com')
        User_model.objects.create(user='existinguser', fname='Exist', lname='User', email='duplicate@example.com', password='somepassword123')

        duplicate_email_data = {
            'username': 'anotheruser',
            'fname': 'Another',
            'lname': 'User',
            'email': 'duplicate@example.com',
            'birthdate': '2000-01-01',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        }

        response = self.client.post(self.register_url, data=duplicate_email_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("This email is already registered" in str(m) for m in messages_list))

        # เช็ค CustomUser แทน
        self.assertFalse(User_model.objects.filter(user='anotheruser').exists())

    def test_register_view_post_integrity_error_other(self):
        from unittest.mock import patch

        valid_data = {
            'username': 'erroruser',
            'fname': 'Error',
            'lname': 'User',
            'email': 'error@example.com',
            'birthdate': '2000-01-01',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        }

        with patch('homepage.views.User.objects.create', side_effect=IntegrityError("unique constraint failed: homepage_user.user")):
            response = self.client.post(self.register_url, data=valid_data)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'register.html')
            messages_list = list(get_messages(response.wsgi_request))
            self.assertTrue(any("There was an error creating your account" in str(m) for m in messages_list))

        # เช็ค CustomUser ว่าไม่ถูกสร้าง
        self.assertFalse(User_model.objects.filter(user='erroruser').exists())

        # ทดสอบหน้า login ด้วยการส่ง GET request เพื่อให้แน่ใจว่าแบบฟอร์มการล็อกอินโหลดได้สำเร็จ
    def test_login_view_get(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertIsInstance(response.context['form'], LoginForm)

    # ทดสอบหน้า login ด้วยการส่งข้อมูล POST ที่ถูกต้อง (happy path)
    def test_login_view_post_valid(self):
        response = self.client.post(self.login_url, data=self.user_credentials)
        self.assertEqual(response.status_code, 302)

    # เพิ่มการทดสอบกรณี session invalid
    # สมมุติว่าต้องการทดสอบกรณีที่ session มี user_id ไม่ถูกต้อง และดูว่าระบบยังคง redirect กลับ login หรือไม่
    def test_login_view_post_valid_with_session_invalid(self):
        # Get the CSRF token first by making a GET request
        response = self.client.get(self.login_url)
        self.csrf_token = response.cookies['csrftoken'].value  # Extract the CSRF token

        # custom_user login
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(
            self.login_url,
            {   
                'csrfmiddlewaretoken': self.csrf_token,
                'username': 'testuser',
                'password': 'testpassword'
            }
        )

        # แก้ session ให้ invalid
        session = self.client.session
        session['user_id'] = 99999  # ค่า user_id ที่ไม่มีในฐานข้อมูล
        session.save()

        # ลอง login อีกรอบด้วย credentials เดิม
        response = self.client.post(self.login_url, data=self.user_credentials)
        # ในกรณีนี้หาก logic ของ login_views ยังไม่ handle ดี อาจจะไปสู่กรณี user not found หรือ error
        # สมมุติว่าหากมีการ redirect กลับ login ถือว่าผ่าน
        #self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/folder', fetch_redirect_response=False)

    # ทดสอบหน้า login ด้วยการส่งข้อมูล POST ที่ไม่ถูกต้อง (sad path)
    def test_login_view_post_invalid(self):
        invalid_credentials = {
            'username': 'wronguser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data=invalid_credentials)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    # ทดสอบหน้า logout เพื่อให้แน่ใจว่าผู้ใช้สามารถล็อกเอาต์และเปลี่ยนเส้นทางไปยังหน้าล็อกอินได้
    def test_logout_view(self):
        self.client.login(**self.user_credentials)
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)

    # ทดสอบการเข้าถึงหน้า admin เมื่อผู้ใช้ที่ล็อกอินเป็น admin
    def test_admin_login(self):
        self.client.login(username='adminuser', password='adminpassword123')
        response = self.client.post(self.login_url, data=self.admin_credentials)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.admin_url)

    # เพิ่มทดสอบกรณี user เป็น staff (เช็ค redirect /admin/)
    def test_login_view_post_staff_user(self):
        # สมมุติเรามี user ที่เป็น staff ใน setUp (หรือสร้างที่นี่)
        staff_user = User.objects.create_user(
            username='staffmember',
            password='staffpassword123',
            is_staff=True
        )
        response = self.client.post(self.login_url, data={
            'username': 'staffmember',
            'password': 'staffpassword123'
        })
        self.assertRedirects(response, '/admin/')

    # เพิ่มทดสอบกรณี AuthUser มีอยู่แต่ CustomUser ไม่เจอ (User not found in the database)
    def test_login_view_user_not_found_in_custom_db(self):
        # สร้าง AuthUser ปกติ
        user = User.objects.create_user(username='testonlyauth', password='authpass')
        # ไม่สร้าง CustomUser ให้สอดคล้อง

        response = self.client.post(self.login_url, data={
            'username': 'testonlyauth',
            'password': 'authpass'
        })
        # คาดว่าควร redirect กลับ login และแจ้งว่าไม่เจอใน database
        self.assertRedirects(response, self.login_url)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("User not found in the database." in str(m) for m in messages_list))

    # เพิ่มทดสอบกรณี form ไม่ valid แต่ username มีใน CustomUser (Invalid Password)
    def test_login_view_invalid_password(self):
        # สมมุติมี User ในระบบพร้อม CustomUser
        auth_user = User.objects.create_user(username='validuser', password='correctpass')
        custom_user = User_model.objects.create(
            user_id=auth_user.id,
            user='validuser',
            fname='Val',
            lname='User',
            email='valuser@example.com',
            password='correctpass'
        )

        # ใส่ password ผิด
        response = self.client.post(self.login_url, data={
            'username': 'validuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Invalid Password" in str(m) for m in messages_list))

    # เพิ่มทดสอบกรณี form ไม่ valid และ username ไม่มีใน CustomUser (Invalid Username)
    def test_login_view_invalid_username(self):
        # ไม่มี User/CustomUser สร้างขึ้น
        response = self.client.post(self.login_url, data={
            'username': 'nouser',
            'password': 'nopassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Invalid Username" in str(m) for m in messages_list))

    # ทดสอบการเข้าถึงหน้า homepage โดยไม่ได้ล็อกอิน
    def test_homepage_view_without_login(self):
        response = self.client.get(self.homepage_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage.html')

    def test_str_user_method(self):
        expected_str = f"{self.user_model.user}"
        self.assertEqual(str(self.user_model), expected_str)

    def test_str_folder_method(self):
        folder = Folder.objects.create(user=self.user_model, folder_name="Test Folder")
        expected_str = f"Folder 1 for User {self.user_model.user}"
        self.assertEqual(str(folder), expected_str)

    def test_str_word_method(self):
        folder = Folder.objects.create(user=self.user_model, folder_name="Test Folder")
        word = Word.objects.create(user=self.user_model, folder=folder, word="Test", meaning="This is a test.")
        expected_str = f"Word 1 in Folder {folder.folder_id} for User {self.user_model.user}"
        self.assertEqual(str(word), expected_str)

    def test_highscore_str_method(self):
        folder = Folder.objects.create(user=self.user_model, folder_name="Test Folder")
        highscore = Highscore.objects.create(user=self.user_model, folder=folder, game_id=1, play_time=1, score=0)
        expected_str = f"{self.user.username} - Folder {folder.folder_id} - Game {highscore.game_id} - Play {highscore.play_time} - Score: {highscore.score}"
        # Check if the string representation matches
        self.assertEqual(str(highscore), expected_str)

class TestUrls(TestCase):  # ใช้ TestCase แทน SimpleTestCase
    def test_homepage_url_resolves(self):
        url = reverse('homepage')
        self.assertEqual(resolve(url).func, homepage)

    def test_about_url_resolves(self):
        url = reverse('about')
        self.assertEqual(resolve(url).func, about)

    def test_register_url_resolves(self):
        url = reverse('register')
        self.assertEqual(resolve(url).func, register)

    def test_login_url_resolves(self):
        url = reverse('login')
        self.assertEqual(resolve(url).func, login_views)

    def test_logout_url_resolves(self):
        url = reverse('logout')
        self.assertEqual(resolve(url).func, logout_views)

    def test_profile_url_resolves(self):
        url = reverse('profile')
        self.assertEqual(resolve(url).func, profile_view)

    def test_password_reset_url_resolves(self):
        url = reverse('password_reset')
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordResetView)

    def test_password_reset_done_url_resolves(self):
        url = reverse('password_reset_done')
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordResetDoneView)

    def test_password_reset_confirm_url_resolves(self):
        url = reverse('password_reset_confirm', kwargs={'uidb64': 'abcd', 'token': '12345'})
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordResetConfirmView)

    def test_password_reset_complete_url_resolves(self):
        url = reverse('password_reset_complete')
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordResetCompleteView)

    # เพิ่ม test สำหรับการเข้าถึงไฟล์ใน media/
    '''def test_media_url_access(self):
        test_file_path = 'profile_pictures/giphy_hvsk0e0.gif'  # ชื่อไฟล์ที่ต้องการทดสอบ
        url = reverse('media_file', kwargs={'file_path': test_file_path})  # สร้าง URL ที่ต้องการทดสอบ
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)  # คาดหวังว่า status code จะเป็น 200 (OK)'''

class TestProfileView(TestCase):
    def setUp(self):
        self.client = Client()
        self.auth_user = AuthUser.objects.create_user(
            username='testuser', 
            password='testpassword'
        )

        self.custom_user = User_model.objects.create(
            user_id=self.auth_user.id, 
            user='testuser', 
            fname='Test', 
            lname='User', 
            email='testuser@example.com',
            password='testpassword'
        )

        self.profile_url = reverse('profile')

        self.login_url = reverse('login')

        # Get the CSRF token first by making a GET request
        response = self.client.get(self.login_url)
        self.csrf_token = response.cookies['csrftoken'].value  # Extract the CSRF token

        # custom_user login
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(
            self.login_url,
            {   
                'csrfmiddlewaretoken': self.csrf_token,
                'username': 'testuser',
                'password': 'testpassword'
            }
        )

    # method tearDown จะถูกเรียกใช้หลังจากทำแต่ละ test case
    # ใช้เพื่อลบไฟล์ test profile picture ที่ใช้ทดสอบการ upload 
    def tearDown(self):
        # ลบไฟล์ profile_picture ถ้ามี
        if self.custom_user.profile_picture:
            file_path = self.custom_user.profile_picture.path
            if os.path.isfile(file_path):
                os.remove(file_path)

    # ทดสอบการอัปเดตข้อมูลสำเร็จ
    def test_profile_view_success(self):

        # test profile picture file
        profile_picture = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61',  # GIF Header
            content_type='image/jpeg'
        )

        data = {
            'action': 'save',
            'user': 'newusername',
            'fname': 'NewFirstName',
            'lname': 'NewLastName',
            'title': 'NewTitle',
            'card_color': '#123456',
            'email': 'newemail@example.com',
            'current_password': 'testpassword',
            'new_password': 'newpassword',
            'profile_picture': profile_picture # upload profile picture
        }

        # เพิ่ม ?edit=true ถ้าจำเป็น เช่น:
        profile_url_with_edit = self.profile_url + '?edit=true'
        response = self.client.post(profile_url_with_edit, data)

        # Fetch updated data
        self.custom_user.refresh_from_db()
        self.auth_user.refresh_from_db()

        # Assert the updates were successful
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(self.custom_user.user, 'newusername')
        self.assertEqual(self.custom_user.fname, 'NewFirstName')
        self.assertEqual(self.custom_user.lname, 'NewLastName')
        self.assertEqual(self.custom_user.title, 'NewTitle')
        self.assertEqual(self.custom_user.card_color, '#123456')
        self.assertEqual(self.custom_user.email, 'newemail@example.com')
        self.assertTrue(self.custom_user.profile_picture.name.endswith('test_image.jpg'))
        self.assertEqual(self.auth_user.username, 'newusername')
        self.assertTrue(self.auth_user.check_password('newpassword'))

    # ทดสอบกรณีพบผู้ใช้ในหน้า profile
    def test_profile_view_user_found(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200) # render status code
        self.assertTemplateUsed(response,'profile.html')  # render profile.html
        self.assertIn('user',response.context) # user ถูกส่งมาในหน้า profile.html


    # ทดสอบกรณีผู้ใช้ไม่พบในระบบ
    def test_profile_view_user_not_found(self):

        session = self.client.session
        session['user_id'] = 99999  # ค่า user_id ที่ไม่มีในฐานข้อมูล
        session.save()

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 302)  # Redirect to login if user not found

    # ทดสอบกรณีชื่อผู้ใช้ใหม่ซ้ำกับผู้ใช้อื่น
    def test_profile_view_username_exists(self):
        another_user = AuthUser.objects.create_user(
            username='existinguser', 
            password='password123'
        )

        User_model.objects.create(
            user_id=another_user.id, 
            user='existinguser', 
            fname='Another', 
            lname='User', 
            email='existinguser@example.com'
        )

        data = {
            'action': 'save',
            'user': 'existinguser',
            'fname': 'NewFirstName',
            'lname': 'NewLastName',
            'title': 'NewTitle',
            'card_color': '#123456',
            'email': 'newemail@example.com',
            'current_password': 'testpassword',
            'new_password': 'newpassword'
        }

        #response = self.client.post(self.profile_url, data)
        response = self.client.post(self.profile_url + '?edit=true', data)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(response.status_code, 302)  # Redirect after error

    # ทดสอบกรณีรหัสผ่านปัจจุบันไม่ถูกต้อง
    def test_profile_view_incorrect_current_password(self):

        data = {
            'action': 'save',
            'user': 'newusername',
            'fname': 'NewFirstName',
            'lname': 'NewLastName',
            'title': 'NewTitle',
            'card_color': '#123456',
            'email': 'newemail@example.com',
            'current_password': 'wrongpassword',
            'new_password': 'newpassword'
        }

        #response = self.client.post(self.profile_url, data)
        response = self.client.post(self.profile_url + '?edit=true', data)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(response.status_code, 302)  # Redirect after error

    # ทดสอบการอัปเดตข้อมูลโดยไม่มีการเปลี่ยนรหัสผ่าน
    def test_profile_view_no_password_change(self):

        data = {
            'action': 'save',
            'user': 'newusername',
            'fname': 'NewFirstName',
            'lname': 'NewLastName',
            'title': 'NewTitle',
            'card_color': '#123456',
            'email': 'newemail@example.com'
        }

        #response = self.client.post(self.profile_url, data)
        response = self.client.post(self.profile_url + '?edit=true', data)

        # Fetch updated data
        self.custom_user.refresh_from_db()
        self.auth_user.refresh_from_db()

        # Assert the updates were successful
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(self.custom_user.user, 'newusername')
        self.assertEqual(self.custom_user.fname, 'NewFirstName')
        self.assertEqual(self.custom_user.lname, 'NewLastName')
        self.assertEqual(self.custom_user.title, 'NewTitle')
        self.assertEqual(self.custom_user.card_color, '#123456')
        self.assertEqual(self.custom_user.email, 'newemail@example.com')
        self.assertEqual(self.auth_user.username, 'newusername')
        self.assertEqual(self.auth_user.email, 'newemail@example.com')

    def test_profile_view_cancel(self):
        data = {
            'action': 'cancel',
            'user': 'cancelusername',
            'fname': 'CancelFirstName',
            'lname': 'CancelLastName',
            'email': 'canceluser@example.com',
        }
        response = self.client.post(self.profile_url + '?edit=true', data)
    
        # คาดหวังว่าไม่ควรมีการบันทึกข้อมูลใหม่ และจะต้องกลับไปที่ View Mode
        self.assertEqual(response.status_code, 302)  # Redirect กลับไปยังหน้า profile
        self.custom_user.refresh_from_db()  # รีเฟรชข้อมูลจากฐานข้อมูล
        self.assertEqual(self.custom_user.user, 'testuser')  # ตรวจสอบว่าไม่ได้เปลี่ยนชื่อผู้ใช้
    
    def test_profile_view_no_action(self):
        data = {
            'user': 'newusername',
            'fname': 'NewFirstName',
            'lname': 'NewLastName',
            'email': 'newemail@example.com',
        }
        response = self.client.post(self.profile_url + '?edit=true', data)
    
        # คาดหวังว่าไม่มีการทำงานใดๆ และแสดงผลลัพธ์ตามปกติ
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertIn('user', response.context)  # ตรวจสอบว่า user ยังแสดงอยู่
    
    # ทดสอบการทิ้งข้อมูล (Discard)
    def test_profile_view_discard_changes(self):
        data = {
            'action': 'discard',
            'user': 'newusername',
            'fname': 'NewFirstName',
            'lname': 'NewLastName',
            'email': 'newemail@example.com',
        }

        response = self.client.post(self.profile_url + '?edit=true', data)

        self.assertEqual(response.status_code, 302)  # Redirect after discard
        self.custom_user.refresh_from_db()
        self.assertEqual(self.custom_user.user, 'testuser')  # Verify data is not saved
