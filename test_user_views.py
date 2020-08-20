"""User model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, connect_db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class UserModelTestCase(TestCase):
    """Test the user experience"""

    def setUp(self):
        """Set up new user"""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.new_user = User.signup(username='test', email='test@email.com',password='password',image_url=None)

        self.new_user_id = 1111
        self.new_user.id = new_user_id

        self.user_two = User.signup(username="usertwo", email="usertwo@test.com", password="password", image_url=None)
        self.user_two_id = 2222
        self.user_two.id = self.user_two_id

        self.user_three = User.signup(username="userthree", email="userthree@test.com", password="password", image_url=None)
        self.user_three_id = 3333
        self.user_three.id = self.user_three_id
        
        self.user_four = User.signup(username="userfour", email="userfour@test.com", password="password", image_url=None)

        db.session.commit()

    def tearDown(self):
        """tear down after test"""
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def setup_likes(self):
        """Sets up a list of likes"""
        message_one = Message(text="trending", user_id=self.new_user_id)
        message_two = Message(text="Eating", user_id=self.new_user_id)
        message_three = Message(id=1234, text="warble", user_id=self.user_two_id)
        db.session.add_all([message_one, message_two, message_three])
        db.session.commit()

        likes = Likes(user_id=self.new_user_id, message_id=1234)

        db.session.add(likes)
        db.session.commit()

    def setup_followers(self):
        """Set up follower & followings"""
        follows = Follows(user_being_followed_id=self.new_user_id, user_following_id=self.user_two_id)
        follows_again = Follows(user_being_followed=self.user_two, user_following_id=self.new_user_id)

        db.session.add([follows, follows_again])
        db.session.commit

    def test_show_all_users(self):
        """Test users being shown"""
        with self.client as client:
            resp = client.get('/users')

            self.assertIn('@test', str(resp.data))
            self.assertIn('@usertwo', str(resp.data))
            self.assertIn('@userthree', str(resp.data))
            self.assertIn('@userfour', str(resp.data))

    def test_user_search(self):
        """Test a user being searched for"""
        with self.client as client:
            resp = client.get('users?q=test')

            self.assertIn('@test', str(resp.data))

            self.assertNotIn('@usertwo', str(resp.data))
            self.assertNotIn('@userthree', str(resp.data))
            self.assertNotIn('@userfour', str(resp.data))

    def test_users_in_page(self):
        """Test a user page"""
        with self.client as client:
            resp = client.get(f'/users/{self.new_user_id}')

            self.asserEqual(resp.status_code, 200)
            self.assertIn('@test', str(resp.data))

    def test_do_likes_show(self):
        """Shows a user liked something"""
        self.setup_likes()

        with self.client as client:
            resp = client.get(f'/users/{self.new_user_id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@test', str(resp.data))
            self.assertIn('<button class="btn btn-sm btn-secondary">', str(resp.data))

    def test_add_like(self):
        """Tests adding a like to database"""
        message = Message(id=2000, text='Testing a like', user_id=self.user_two_id)
        
        db.session.add(message)
        db.session.commit()

        with self.client as client:
            #Store key in session as its needed in our routes!
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.new_user_id

            resp = client.post('/users/add_like/2000', follow_redirects=True)
            
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id == 2000).all()

            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.new_user_id)

    def test_remove_likes(self):
        """Can we remove a liked warble? Yes we can"""
        self.setup_likes()

        message = Message.query.filter(Message.text=='warble')
        
        #get message back
        self.assertIsNotNone(message)
        #make sure user is not messages's author, as that negates a like
        self.assertNotEqual(message.user_id, self.new_user_id)

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.new_user_id

            resp = client.post(f'/users/likes/delete/{message.id}', follows_redirects=True)

            self.asserEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.user_id == self.new_user_id)
            #Should be 0, since we removed the like!
            self.assertEqual(len(likes), 0)

    def test_unauthorized_like_access(self):
        """Test if routes handle unathorized removal"""
        with self.client as client:
            resp = client.get(f'/users/{self.new_user_id}/likes', follows_redirects=True)

            self.assertEqual(resp.status_code, 301)
            self.assertIn('Access unauthorized', str(resp.data))
    
    def test_unauthorized_message_access(self):
        """Test if routes handle unathorized removal"""
        with self.client as client:
            resp = client.get(f'/messages/new', follows_redirects=True)

            self.assertEqual(resp.status_code, 301)
            self.assertIn('Access unauthorized', str(resp.data))

    def test_show_follower(self):
        """Shows user's cult following"""
        self.setup_followers()

        with self.client as client:
            with client.session_transaction() as sesssion:
                session[CURR_USER_KEY] = self.new_user_id

            resp = client.get(f"/users/{self.new_user_id}/followers")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@usertwo", str(resp.data))
            self.assertNotIn("@userthree", str(resp.data))
            self.assertNotIn("@userfour", str(resp.data))
            self.assertNotIn("@test", str(resp.data))

    def test_show_following(self):
        """Shows who the user follows"""
        self.setup_followers()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.new_user_id

            resp = c.get(f"/users/{self.new_user_id}/following")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@usertwo", str(resp.data))
            self.assertNotIn("@userthree", str(resp.data))
            self.assertNotIn("@userfour", str(resp.data))
            self.assertNotIn('@test', str(res.data))