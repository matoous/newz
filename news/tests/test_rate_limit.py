import unittest

from news import real_make_app

TEST_DB = 'test.db'


class BasicTests(unittest.TestCase):

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

    def test_rate_limit(self):
        pass


if __name__ == "__main__":
    unittest.main()