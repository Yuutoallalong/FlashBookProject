from django.db import models
from django.contrib.auth.hashers import make_password
from datetime import date, timedelta
# Create your models here.

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    user = models.CharField(max_length=50)
    fname = models.CharField(max_length=50)
    lname = models.CharField(max_length=50)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    day_streak = models.IntegerField(default=0)
    day_streak_left = models.IntegerField(default=0)
    last_check_in = models.DateField(null=True, blank=True)
    credits = models.PositiveIntegerField(default=0)

    title = models.CharField(max_length=100, null=True, blank=True)
    title_ava = models.JSONField(default=list, blank=True)

    card_color = models.TextField(default='#ffffff') 
    card_color_ava = models.JSONField(default=list, blank=True)
    
    hint_ava = models.IntegerField(default=0)
    
    is_admin = models.BooleanField(default=False)

    # method for hash password
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_in(self):
        today = date.today()
        if not self.last_check_in:
            self.day_streak = 1
            self.day_streak_left = 1
        else:
            # ถ้าเช็คอินในวันที่ต่อจากเมื่อวาน
            if self.last_check_in + timedelta(days=1) == today:
                self.day_streak += 1
                self.day_streak_left += 1

            elif self.last_check_in != today:
                self.day_streak = 1
                self.day_streak_left = 1

        self.last_check_in = today
        self.save()

    def get_title_ava(self):
        return self.title_ava  # รับค่า list ที่เก็บใน JSONField

    def set_title_ava(self, titles):
        self.title_ava = titles  # บันทึกค่าลงใน JSONField

    def get_card_color_ava(self):
        return self.card_color_ava  # รับค่า list ที่เก็บใน JSONField

    def set_card_color_ava(self, colors):
        self.card_color_ava = colors 

    def __str__(self):
        return self.user

# user1 = User.objects.get(user="john_doe")
# Folder.objects.create(user=user1, folder_name="Vocabulary")

class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder_id = models.IntegerField()
    folder_name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('user', 'folder_id')  # Composite unique key

    def save(self, *args, **kwargs):
        if not self.folder_id:
            last_folder = Folder.objects.filter(user=self.user).order_by('folder_id').last()
            self.folder_id = last_folder.folder_id + 1 if last_folder else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Folder {self.folder_id} for User {self.user.user}"

# Word.objects.create(user=user1, folder=folder1, word="loquacious", meaning="tending to talk a great deal")

class Word(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    word_id = models.IntegerField()
    word = models.CharField(max_length=100)
    meaning = models.CharField(max_length=255)

    class Meta:
        unique_together = ('user', 'folder', 'word_id')  # Composite unique key

    def save(self, *args, **kwargs):
        if not self.word_id:
            last_word = Word.objects.filter(user=self.user, folder=self.folder).order_by('word_id').last()
            self.word_id = last_word.word_id + 1 if last_word else 1
        super().save(*args, **kwargs)
    
    @staticmethod
    def reorder_word_ids(user, folder):
        # ลำดับ word_id ใหม่ทุกครั้งหลังจากการลบข้อมูล
        words = Word.objects.filter(user=user, folder=folder).order_by('word_id')
        for index, word in enumerate(words, start=1):  # เริ่มนับจาก 1
            if word.word_id != index:
                word.word_id = index
                word.save()

    def __str__(self):
        return f"Word {self.word_id} in Folder {self.folder.folder_id} for User {self.user.user}"


class Highscore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)

    game_id = models.PositiveSmallIntegerField()
    # only 1 and 2 are valid numbers
    # 1 will be flashcard and 2 will be wordguesss

    play_time = models.IntegerField()
    score = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'folder', 'game_id', 'play_time'], name='unique_user_folder_game_play'),
            models.CheckConstraint(check=models.Q(game_id__in=[1, 2, 3]), name='valid_game_id')
        ]

    def save(self, *args, **kwargs):
        if not self.play_time:
            last_play = Highscore.objects.filter(user=self.user, folder=self.folder, game_id=self.game_id).order_by('play_time').last()
            self.play_time = last_play.play_time + 1 if last_play else 1

        all_scores = Highscore.objects.filter(user=self.user, folder=self.folder, game_id=self.game_id).order_by('play_time')
        
        if all_scores.count() >= 15:
            all_scores.first().delete()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.user} - Folder {self.folder.folder_id} - Game {self.game_id} - Play {self.play_time} - Score: {self.score}"


# user1 = User.objects.get(user="john_doe")
# folder1 = Folder.objects.get(user=user1, folder_id=1)

# # First game entry for user1, folder1, game_id 1
# highscore1 = Highscore.objects.create(user=user1, folder=folder1, game_id=1, score=85)  # play_time will be 1

# # Second play for the same user, folder, and game_id
# highscore2 = Highscore.objects.create(user=user1, folder=folder1, game_id=1, score=90)  # play_time will be 2

# # New game_id for the same user and folder
# highscore3 = Highscore.objects.create(user=user1, folder=folder1, game_id=2, score=88)  # play_time will be 1

# # Third play for the original game_id (user1, folder1, game_id=1)
# highscore4 = Highscore.objects.create(user=user1, folder=folder1, game_id=1, score=92)  # play_time will be 3

class PublicGame(models.Model):

    GAME_STATUS_CHOICES = [
    ('OPEN', 'Open'),
    ('FINISHED', 'Finished'),
    ]

    GAME_TYPE_CHOICES = [
        ('FLASHCARD', 'Flashcard'),
        ('FLASHCARDCHOICE', 'Flashcard Choice'),
        ('WORDGUESS_EASY', 'Wordguess Easy'),
        ('WORDGUESS_NORMAL', 'Wordguess Normal'),
        ('WORDGUESS_HARD', 'Wordguess Hard'),
    ]
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    max_players = models.PositiveIntegerField()
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    start_time = models.DateTimeField()  
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=10,
        choices=GAME_STATUS_CHOICES,
        default='OPEN',
    ) 

    game_type = models.CharField(
        max_length=20,
        choices=GAME_TYPE_CHOICES,
        default='FLASHCARD'
    )

    players = models.ManyToManyField(User, through='GamePlayer', related_name='games')

    def __str__(self):
        return self.name


class GamePlayer(models.Model):

    game = models.ForeignKey(PublicGame, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('game', 'user')

    def __str__(self):
        return f'{self.user.user} - {self.game.name}'