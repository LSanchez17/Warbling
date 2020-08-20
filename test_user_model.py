"""User model tests."""

# run these tests like:
#
# python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        #Create two mock users, and commit to test db
        user_one = User.signup('user1','user1@email.com', 'password', '')
        user_one_id = 11111
        user_one.id = user_one_id

        user_two = User.signup('user2','user2@email.com', 'password', '')
        user_two_id = 22222
        user_two.id = user_one_id

        db.session.commit()

        #Store the user objects into two variables
        user_one = User.query.get(user_one_id)
        user_two = User.query.get(user_two_id)

        #Not sure why we are instancing these again
        self.user_one = user_one
        self.user_two = user_two

        self.client = app.test_client()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_follows(self):
        """We make sure a user can actually follow another"""
        self.user_one.following.append(self.user_two)
        db.session.commit()

        #Assert that user two has one follower, and not following anyone
        #Assert user one has no followers and is following one person
        self.assertEqual(len(self.user_two.following), 0)
        self.assertEqual(len(self.user_two.followers), 1)
        self.assertEqual(len(self.user_one.followers), 0)
        self.assertEqual(len(self.user_one.following), 1)

        #Checking the following/followers relation in the model to see if it matches
        self.assertEqual(self.user_two.followers[0].id, self.user_one.id)
        self.assertEqual(self.user_one.following[0].id, self.user_two.id)

    def test_user_is_following(self):
        """Test is following methods"""
        self.user_one.following.append(self.user_two)
        db.session.commit()

        self.assertTrue(self.user_one.is_following(self.user_two))
        self.asserFalse(self.user_two.is_following(self.user_one))

    def test_is_followed(self):
        """Tests following methods"""
        self.user_one.following.append(self.user_two)
        db.session.commit()

        self.assertTrue(self.user_two.is_followed_by(self.user_one))
        self.assertFalse(self.user_one.is_followed_by(self.user_two))


    def test_valid_signup(self):
        """Tests a valid user can sign up"""
        user_test = User.signup('TestID', 'Testing@test.com', 'testpass', '')
        user_id = 00000
        user_test.id = user_id
        
        db.session.commit()

        user_test = User.query.get(user_id)

        #Make sure parts of the user that signed up match
        self.assertIsNotNone(user_test)
        self.assertEqual(user_test.username, 'TestID')
        self.assertEqual(user_test.email, ' Testing@test.com')
        self.assertNotEqual(user_test.password, ' testpass')
        self.assertTrue(user_test.password.startswith('$2b$'))


    def test_invalid_signup(self):
        """Test bad signup fails"""
        bad_signup = User.signup(None, None, None, None)
        user_id = 00000
        bad_signup.id = user_id

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
        
    def test_authentication(self):
        """Tests user password authentication"""
        user = User.authenticate(self.user_one.username, 'password')
        #Tests that the user can sign in with a proper password 
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user_one_id)
    
    def test_bad_username(self):
        """Test bad username fails on login"""
        self.assertFalse(User.authenticate('dont-exist','password'))

    def test_bad_password(self):
        """Test bad password fails on login"""
        self.assertFalse(User.authenticate(self.user_one.username, 'notarealpassword'))













