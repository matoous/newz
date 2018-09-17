import unittest

from news import real_make_app

TEST_DB = 'test.db'


class AuthTests(unittest.TestCase):

    def setUp(self):
        app = real_make_app()
        app.config['TESTING'] = True
        app.config['DEBUG'] = False

        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_registration(self):
        # try successfully registering new user
        rv = self.app.post("/join", data=dict(useranme='testuser', email='testuser@testuser.tu', password='testuser'), follow_redirects=True)
        assert b'testuser' in rv.data and b'logout' in rv.data

        # error empty username
        rv = self.app.post("/join", data=dict(email='testuser2@testuser.tu', password='testuser2'), follow_redirects=True)
        assert b'select username' in rv.data

        # short username
        rv = self.app.post("/join", data=dict(useranme='t', email='testuser2@testuser.tu', password='testuser2'), follow_redirects=True)
        assert b'must be between 3 and 20 characters long' in rv.data

        #duplicate username
        rv = self.app.post("/join", data=dict(useranme='testuser', email='testuser2@testuser.tu', password='testuser2'), follow_redirects=True)
        assert b'username is already taken' in rv.data

        # empty email
        rv = self.app.post("/join", data=dict(useranme='testuser', password='testuser2'), follow_redirects=True)
        assert b'You have to enter your email' in rv.data

        # duplicate email
        rv = self.app.post("/join", data=dict(useranme='testuser2', email='testuser@testuser.tu', password='testuser2'), follow_redirects=True)
        assert b'email already taken' in rv.data

        # empty password
        rv = self.app.post("/join", data=dict(useranme='testuser2', email='testuser@testuser.tu'), follow_redirects=True)
        assert b'email already taken' in rv.data

        # short password
        rv = self.app.post("/join", data=dict(useranme='testuser2', email='testuser@testuser.tu', password='as'), follow_redirects=True)
        assert b'Password must be at least 6 characters long' in rv.data

if __name__ == "__main__":
    unittest.main()