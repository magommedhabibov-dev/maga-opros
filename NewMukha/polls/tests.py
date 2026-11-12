from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import Choice, Question


class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        future_question = Question(pub_date=timezone.now() + timedelta(days=30))
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        old_question = Question(pub_date=timezone.now() - timedelta(days=2))
        self.assertIs(old_question.was_published_recently(), False)


class PollViewTests(TestCase):
    def setUp(self):
        self.question = Question.objects.create(
            question_text='Какой вариант вам нравится?',
            pub_date=timezone.now(),
        )
        self.first_choice = Choice.objects.create(
            question=self.question,
            choice_text='Первый',
        )
        self.second_choice = Choice.objects.create(
            question=self.question,
            choice_text='Второй',
        )

    def test_home_redirects_to_poll_list(self):
        response = self.client.get('/')

        self.assertRedirects(response, '/polls/')

    def test_index_shows_published_questions_but_not_future_questions(self):
        future_question = Question.objects.create(
            question_text='Будущий опрос',
            pub_date=timezone.now() + timedelta(days=1),
        )

        response = self.client.get('/polls/')

        self.assertContains(response, self.question.question_text)
        self.assertContains(response, '/static/polls/site.css')
        self.assertNotContains(response, future_question.question_text)

    def test_vote_increments_selected_choice_and_shows_results(self):
        response = self.client.post(
            f'/polls/{self.question.id}/vote/',
            {'choice': self.first_choice.id},
        )

        self.assertRedirects(response, f'/polls/{self.question.id}/results/')
        self.first_choice.refresh_from_db()
        self.assertEqual(self.first_choice.votes, 1)

    def test_vote_without_choice_shows_error(self):
        response = self.client.post(f'/polls/{self.question.id}/vote/', {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Вы не выбрали вариант ответа.')

    def test_results_show_vote_percentages(self):
        self.first_choice.votes = 3
        self.first_choice.save()
        self.second_choice.votes = 1
        self.second_choice.save()

        response = self.client.get(f'/polls/{self.question.id}/results/')

        self.assertContains(response, '75%')
        self.assertContains(response, '25%')
        self.assertContains(response, 'Уже высказались: 4.')
