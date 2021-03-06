from app import Application
from database.models import migrator, User, Thread, Reply, Channel
from database.model_factory import Factory
from tests.base import BaseTest


class ThreadsTest(BaseTest):
    def get_app(self):
        return Application()

    def setUp(self):
        super().setUp()
        migrator.upgrade()
        self.thread = Factory(Thread).create()

    def tearDown(self):
        super().tearDown()
        migrator.downgrade()

    def test_a_user_can_view_all_threads(self):
        response = self.fetch('/threads/')
        self.assertIn(self.thread.title.encode(), response.body)

    def test_a_user_can_read_a_single_thread(self):
        response = self.fetch(self.thread.path)
        self.assertIn(self.thread.title.encode(), response.body)

    def test_a_user_can_read_replies_that_are_associated_with_a_thread(self):
        reply = Factory(Reply).create()
        response = self.fetch(reply.thread.path)
        self.assertIn(reply.body.encode(), response.body)

    def test_a_thread_has_replies(self):
        self.assertIsNotNone(self.thread.replies)

    def test_a_thread_has_a_creator(self):
        self.assertIsInstance(self.thread.user, User)

    def test_a_thread_can_add_a_reply(self):
        self.thread.add_reply({
            'body': 'egg',
            'user': 1,
        })
        self.assertIsNotNone(self.thread.replies)

    def test_a_thread_belongs_to_a_channel(self):
        self.assertIsInstance(self.thread.channel, Channel)

    def test_a_thread_can_make_a_string_path(self):
        self.assertEqual(
            f'/threads/{self.thread.channel.slug}/{self.thread.id}', self.thread.path)  # noqa 501

    def test_a_user_can_filter_threads_according_to_a_channel(self):
        channel = Factory(Channel).create()
        thread_in_channel = Factory(Thread).create()
        thread_in_channel.channel = channel
        thread_in_channel.save()
        thread_not_in_channel = Factory(Thread).create()
        response = self.fetch(f'/threads/?channel={channel.slug}')
        self.assertIn(thread_in_channel.title.encode(), response.body)
        self.assertNotIn(thread_not_in_channel.title.encode(), response.body)

    def test_a_user_can_filter_threads_by_any_username(self):
        user = Factory(User).create()
        thread_by_user = Factory(Thread).create()
        thread_by_user.user = user
        thread_by_user.save()
        thread_not_by_user = Factory(Thread).create()
        response = self.fetch(
            f'/threads/?by={user.username}',
            headers={
                'Cookie': self.be.headers['Set-Cookie'],
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        )
        self.assertIn(thread_by_user.title.encode(), response.body)
        self.assertNotIn(thread_not_by_user.title.encode(), response.body)

    def test_a_user_can_filter_threads_by_popularity(self):
        thread_with_three_replies = Factory(Thread).create()
        replies = Factory(Reply, 3).create()
        for reply in replies:
            reply.thread = thread_with_three_replies
            reply.save()

        thread_with_two_replies = Factory(Thread).create()
        replies = Factory(Reply, 2).create()
        for reply in replies:
            reply.thread = thread_with_two_replies
            reply.save()

        thread_with_one_reply = self.thread
        reply = Factory(Reply).create()
        reply.thread = thread_with_one_reply
        reply.save()

        response = self.fetch('/threads/?popular=1')
        self.assertIn('\n3\ncomments\n'.encode(), response.body)
        self.assertIn('\n2\ncomments\n'.encode(), response.body)
        self.assertIn('\n1\ncomment\n'.encode(), response.body)
