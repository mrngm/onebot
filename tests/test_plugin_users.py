#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_onebot
----------------------------------

Tests for `onebot` module.
"""
from __future__ import unicode_literals

import pytest
import unittest

from irc3.testing import BotTestCase, patch


class UsersPluginTest(BotTestCase):

    config = {
        'includes': ['onebot.plugins.users'],
        'cmd': '!',
    }

    @patch('pymongo.MongoClient')
    def setUp(self, mock):
        self.callFTU()
        self.users = self.bot.get_plugin('onebot.plugins.users.UsersPlugin')

    def test_join(self):
        self.bot.dispatch(':bar!foo@host JOIN #chan')
        user = self.bot.get_user('bar')
        assert user.nick == 'bar'
        assert user.host == 'foo@host'
        assert user.mask.host == 'foo@host'
        assert user.mask.nick == 'bar'
        assert user.channels == set(('#chan',))
        self.bot.dispatch(':bar!foo@host JOIN #chan2')
        assert user.channels == set(('#chan', '#chan2'))

    def test_join_part(self):
        self.bot.dispatch(':bar!foo@host JOIN #chan')
        assert '#chan' in self.users.channels
        self.bot.dispatch(':bar!foo@host JOIN #chan2')
        assert self.bot.get_user('bar').channels == set(('#chan', '#chan2'))
        self.bot.dispatch(':bar!foo@host PART #chan')
        assert self.bot.get_user('bar').channels == set(('#chan2',))
        self.bot.dispatch(':bar!foo@host PART #chan2')
        with pytest.raises(KeyError):
            self.bot.get_user('bar')

        # make sure unknowns don't break things
        self.bot.dispatch(':anon!dont@know PART #chan')

    def test_nick_change(self):
        self.bot.dispatch(':bar!foo@host JOIN #chan')
        self.bot.dispatch(':bar!foo@host NICK bar2')
        user = self.bot.get_user('bar2')
        assert user.nick == 'bar2'
        assert user.host == 'foo@host'
        # test other user gone
        with pytest.raises(KeyError):
            self.bot.get_user('bar')

        # Make sure we don't need to know the person
        self.bot.dispatch(':anonymous!dont@know NICK anon')

    def test_quit(self):
        self.bot.dispatch(':bar!foo@host JOIN #chan')
        self.bot.dispatch(':bar!foo@host QUIT :quitmessage')
        with pytest.raises(KeyError):
            self.bot.get_user('bar')

        self.bot.dispatch(':bar!foo@host JOIN #chan')
        msg = ':{}!foo@bar QUIT :quitmsg'.format(self.bot.nick)
        self.bot.dispatch(msg)
        with pytest.raises(KeyError):
            self.bot.get_user('bar')
        assert self.users.channels == set()

    def test_who(self):
        # Only accept these if we're in that channel
        self.bot.dispatch(':server 352 irc3 #chan ~user host serv bar H@ :hoi')
        assert len(self.users.active_users) == 0

        self.users.channels.add('#chan')
        self.bot.dispatch(':server 352 irc3 #chan ~user host serv bar H@ :hoi')
        user = self.bot.get_user('bar')
        assert user.nick == 'bar'
        assert user.host == '~user@serv'
        assert user.channels == set(('#chan',))


if __name__ == '__main__':
    unittest.main()
