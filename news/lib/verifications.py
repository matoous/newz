from secrets import token_urlsafe

from flask import current_app

from news.lib.cache import cache
from news.lib.mail import registration_email, send_mail
from news.lib.task_queue import q

EMAIL_VERIFICATION_EXPIRE = 60*60* 48  # 48 hours


class EmailVerification:
    """
    Email Verification handles email verifications
    """

    def __init__(self, user=None, token=''):
        self.user = user
        self.token = token

    def verify(self):
        """
        Checks if given verification exists
        :return: 
        """
        return cache.get(self._cache_key, raw=True) is not None

    @property
    def user_id(self):
        """
        Returns ID of user for whom this verification applies
        :return: user ID
        """
        return int(cache.get(self._cache_key, raw=True))

    @property
    def _cache_key(self):
        """
        Cache key for email verification
        :return: cache key
        """
        return 'e_verify:{}'.format(self.token)

    @property
    def _url(self):
        """
        Formatted URL with verification link
        :return:
        """
        return "localhost:5000/verify/{}".format(self.token)

    def create(self):
        """
        Creates email verification which expires after given time
        and sends email to user to verify his email
        """

        # create token
        self.token = token_urlsafe(16)

        # save token to redis for limited time
        cache.set(self._cache_key, self.user.id, ttl=EMAIL_VERIFICATION_EXPIRE, raw=True)

        # send email with verification link
        msg = registration_email(self.user, self._url)
        q.enqueue(send_mail, msg, result_ttl=0)
