import unittest
import UserDict

from will.plugin import WillPlugin
from will.decorators import respond_to

# ----------------------------------------------------------------------
#  The plugin
# ----------------------------------------------------------------------

class BoardManager(WillPlugin):
    """A general resource allocation plugin."""

    def __init__(self):
        self.resources = {}

    @respond_to('add resource (?P<resource>\S+)', admin_only=True)
    def add_resource(self, message, resource=None):
        if not resource:
            self.reply(message, "Add WHAT, exactly?")
            return

        if resource in self.resources:
            self.reply(message, 'Resource already in the list, dummy')
            return

        self.resources[resource] = []
        self.reply(message, 'Resource "{resource}" added.'.format(
            resource=resource))
        return

    @respond_to('remove resource (?P<resource>\S+)', admin_only=True)
    def remove_resource(self, message, resource=None):
        if not resource:
            self.reply(message, "Remove WHAT, exactly?")
            return

        if resource not in self.resources:
            self.reply(message, 'I know nothing about that resource.')
            return

        del self.resources[resource]
        self.reply(message, 'Resource removed')
        return

    @respond_to('request (?P<resource>\S+)')
    def request(self, message, resource=None):
        if not resource:
            self.reply(message, 'I can\'t get an empty resource. Think '
                       'a bit more before asking for something.')
            return

        if resource not in self.resources:
            self.reply(message, 'I never heard of "{resource}", is it '
                       'something you can eat?'.format(resource=resource))
            return

        if message.sender.nick in self.resources[resource]:
            self.reply(message, 'You\'re already in the list, no need to '
                       'ask for it again.')
            return

        user_resource = self._user_resource(message.sender.nick)
        if user_resource:
            self.reply(message, 'stop being greedy and free {resource} '
                       'first.'.format(resource=user_resource))
            return

        if not self.resources[resource]:
            self.reply(message, 'There is no one using it, you\'re free '
                       'to go.')
        else:
            self.reply(message, '{user} is using it right now, you\'re '
                       'user {position} in the {resource} list.'.format(
                           user=self.resources[resource][0],
                           position=len(self.resources[resource]),
                           resource=resource))

        self.resources[resource].append(message.sender.nick)
        return

    @respond_to('done')
    def done(self, message):
        used_resource = self._user_resource(message.sender.nick)
        if not used_resource:
            self.reply(message, 'I didn\'t even know you were using something!')
            return

        # what can happen here:
        # 1) the user was not the first in the list: just remove them and be
        # done with it.
        # 2) the user is the first in the list: we remove the resource from
        # them but:
        # 2.1) If the list is not empty after that, we alert the next one in
        # the list (the new first person in the list)
        # 2.2) If the list gets empty, we alert everyone that the resource is
        # free to everyone

        if self.resources[used_resource][0] != message.sender.nick:
            self.resources[used_resource].remove(message.sender.nick)
            self.reply('Ok, you\'re out of the list for resource '
                       '{resource}'.format(resource=used_resource))
            return

        # we know it's the first in the list, we can just pop() it out
        self.resources[used_resource].pop(0)

        if len(self.resources[used_resource]) > 0:
            self.say('@{user} there is no one using {resource} right now, '
                     'you\'re free to go.'.format(
                         user=self.resources[used_resource][0],
                         resource=used_resource))
            return

        self.say('@all {resource} is free to use, just ask it.'.format(
            resource=used_resource))
        return

    @respond_to('(?P<resource>\S+) is free\?')
    def is_free(self, message, resource):
        return

    def _user_resource(self, user):
        """Return the resource the user is using right now. If the user is not
        using any resources, return None."""
        used_resource = None
        for resource in self.resources:
            if user in self.resources[resource]:
                used_resource = resource
                break
        return used_resource


# ----------------------------------------------------------------------
#  The tests
# ----------------------------------------------------------------------

class ObjDict(UserDict.UserDict):
    def __getattr__(self, key):
        return self.data[key]

class TestBoardManager(unittest.TestCase):
    def setUp(self):
        self.robot = BoardManager()
        self.last_message = None

        self.message_user_1 = ObjDict({'type': 'groupchat',
                                       'sender': ObjDict(
                                           {'nick': 'TestRobot'})})
        self.message_user_2 = ObjDict({'type': 'groupchat',
                                       'sender': ObjDict(
                                           {'nick': 'AnotherUser'})})
        self.message_all = ObjDict({'type': 'groupchat',
                                    'sender': ObjDict({'nick': 'all'})})
        self.robot.say = self._mocked_say

    def _mocked_say(self, content, message=None, **kwargs):
        """'Mocked' reply function, so we don't need to create a real "message"
        object."""
        self.last_message = content
        return

    def test_add_resource(self):
        """Test if adding a resource actually adds a resource."""
        self.robot.add_resource(self.message_user_1, 'A'),
        self.assertLastMessage('Resource "A" added.')
        self.assertTrue('A' in self.robot.resources)
        return

    def test_add_no_resource(self):
        """Test if the bot complains about an add resource with a resource."""
        self.robot.add_resource(self.message_user_1)
        self.assertLastMessage('Add WHAT, exactly?')
        self.assertTrue(not self.robot.resources)
        return

    def test_add_an_existing_resource(self):
        """Test if the bot complains about an attemp to add a resource that is
        already in the list."""
        self.robot.add_resource(self.message_user_1, 'A')
        self.robot.add_resource(self.message_user_1, 'A')
        self.assertLastMessage('Resource already in the list, dummy')
        self.assertTrue('A' in self.robot.resources)
        return

    def test_remove_resource(self):
        """Test if removing a remove actually removes it."""
        self.robot.add_resource(self.message_user_1, 'A')
        self.robot.remove_resource(self.message_user_1, 'A')
        self.assertLastMessage('Resource removed')
        self.assertTrue('A' not in self.robot.resources)
        return

    def test_remove_unknown_resource(self):
        """Test error message when trying to remove a resource that doesn't
        exist."""
        self.robot.remove_resource(self.message_user_1, 'A')
        self.assertLastMessage('I know nothing about that resource.')
        return

    def test_request_resource(self):
        """Test if you can request a resource."""
        self.robot.add_resource(self.message_user_1, 'A')
        self.robot.request(self.message_user_1, 'A')
        self.assertLastMessage('There is no one using it, '
                               'you\'re free to go.')
        return

    def test_request_unknown_resource(self):
        """Test if the bot complains when you try to get something that
        doesn't exist."""
        self.robot.request(self.message_user_1, 'A')
        self.assertLastMessage('I never heard of "A", is it something you '
                               'can eat?')
        return

    def test_request_used_resource(self):
        """Test if the user is added in the waiting list when there is someone
        already using the resource."""
        self.robot.add_resource(self.message_user_1, 'A')
        self.robot.request(self.message_user_1, 'A')
        self.robot.request(self.message_user_2, 'A')
        self.assertLastMessage('{first_user} is using it right now, '
                               'you\'re user 1 in the A list.'.format(
                                   first_user=self.message_user_1.sender.nick,
                               ),
                               self.message_user_2)
        return

    def test_request_resource_already_requested(self):
        """Test if the bot complains about trying to request a resource
        twice."""
        self.robot.add_resource(self.message_user_1, 'A')
        self.robot.request(self.message_user_1, 'A')
        self.robot.request(self.message_user_1, 'A')
        self.assertLastMessage('You\'re already in the list, no need to '
                               'ask for it again.')
        return

    def test_request_two_resources(self):
        """Test if the bot blocks requesting two resources at the same
        time."""
        self.robot.add_resource(self.message_user_1, 'A')
        self.robot.add_resource(self.message_user_1, 'B')
        self.robot.request(self.message_user_1, 'A')
        self.robot.request(self.message_user_1, 'B')
        self.assertLastMessage('stop being greedy and free A first.')
        return

    def test_done(self):
        """Test if the bot releases the resources when requested."""
        self.robot.add_resource(self.message_user_1, 'A')
        self.robot.request(self.message_user_1, 'A')
        self.robot.done(self.message_user_1)
        self.assertLastMessage('A is free to use, just ask it.',
                               self.message_all)
        return

    def test_done_has_nothing(self):
        """Test if the bot complains if you try to release a resource you
        never had."""
        self.robot.add_resource(self.message_user_1, 'A')
        self.robot.done(self.message_user_1)
        self.assertLastMessage('I didn\'t even know you were using '
                               'something!')
        return

    def test_done_alert_other(self):
        """Test if the bot informs the second user in the list that the
        resource is free."""
        self.robot.add_resource(self.message_user_1, 'A')
        self.robot.request(self.message_user_1, 'A')
        self.robot.request(self.message_user_2, 'A')
        self.robot.done(self.message_user_1)
        self.assertLastMessage('there is no one using A right now, '
                               'you\'re free to go.',
                               self.message_user_2)
        return

    # helpers
    def assertLastMessage(self, message, reply_to=None):
        """Check if the last received message is the one we expect."""
        if reply_to is None:
            reply_to = self.message_user_1

        self.assertEquals(self.last_message, '@' + reply_to.sender.nick +
                          ' ' + message)
        return

if __name__ == '__main__':
    unittest.main()
