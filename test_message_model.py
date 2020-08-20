import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, donnect_db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Tests message model"""

    def setUp(self):
        """Create set up for each test run"""
        db.drop_all()
        db.create_all()

        self.user_id = 0000
        user = User.signup('test_user'. 'testing@test.com','password','')
        user.id = self.user_id

        db.session.commit()

        self.user = User.query.get(self.user_id)

        self.client = app.test_client()

    def tearDown(self):
        """Teardown after each individual test"""
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_message_model(self):
        """Test that the model works"""

        message = Message(text='a simple message'. user_id = self.user_id)

        db.session.add(message)
        db.session.commit()

        #We test that the messages relation to user has one item and its contetns
        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, 'a simple message')

    def test_message_likes(self):
        """Test a message being liked"""
        message_one = Message(text='first message', user_id=self.user_id)
        message_two = Message(text='second message', user_id=self.user_id)

        other_user = User.signup('likingaccount', 'like@email.com', 'ilikewarble', '')
        other_user_id = 9999
        other_user.id = other_user_id

        db.session.add_all([message_one, message_two, other_user])
        db.session.commit()

        other_user.likes.append(message_one)
        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == other_user_id).all()

        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, message_one.id)
        self.assertNotEqual(len(likes), 2)
        self.assertFalse(likes[1].message_id, message_two.id)