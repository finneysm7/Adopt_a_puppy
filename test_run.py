from run import app

import unittest

#import an XML parser
from xml.etree import ElementTree

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        app.config['SECRET_KEY'] = 'sekrit!'
        self.test_app = app.test_client(self)

    def assertTwiML(self, response):
        # Check for error.
        self.assertEquals(response.status, "200 OK")

        # Parse the result into an ElementTree object
        root = ElementTree.fromstring(response.data)

        # Assert the root element is a Response tag
        self.assertEquals(root.tag, 'Response',
                          "Did not find  tag as root element " \
                          "TwiML response.")

    def message(self, body, url='/message', to="+15550001111",
                from_='+15558675309', extra_params={}):
        """Simulates Twilio Message request to Flask test client

        Args:
            body: The contents of the message received by Twilio.

        Keyword Args:
            url: The webhook endpoint you wish to test. (default '/sms')
            to: The phone number being called. (default '+15550001111')
            from_: The CallerID of the caller. (default '+15558675309')
            extra_params: Dictionary of additional Twilio parameters you
                wish to simulate, like MediaUrls. (default: {})

        Returns:
            Flask test client response object.
        """

        # Set some common parameters for messages received by Twilio.
        params = {
            'MessageSid': 'SMtesting',
            'AccountSid': 'ACxxxxxxx',
            'To': to,
            'From': from_,
            'Body': body,
            'NumMedia': 0,
            'FromCity': 'BROOKLYN',
            'FromState': 'NY',
            'FromCountry': 'US',
            'FromZip': '55555'}

        # Add extra params not defined by default.
        if extra_params:
            params = dict(params.items() + extra_params.items())

        # Return the app's response.
        return self.test_app.post(url, data=params)

    def test_endpoint(self):
        response = self.message('anything', url='/')
        self.assertTwiML(response)

    def test_send_pet_valid(self):
        # Create a new test that validates
        response = self.message('anything',url='/')

        # Parse the result into an ElementTree object
        root = ElementTree.fromstring(response.data)

        # Assert response has one message verb
        message_query = root.findall('Message')
        self.assertEquals(len(message_query), 1,
                          "Did not find one Message verb, instead found: %i " %
                          len(message_query))

        # Assert Message verb has two nouns
        message_children = list(message_query[0])
        self.assertEquals(len(message_children), 2,
                          "Message does not have two nouns, instead found: %s" %
                          len(message_children))

        # Assert Message verb has body
        self.assertEquals(message_children[0].tag, 'Body',
                          "Message does not have a body, instead found: %s" %
                          message_children[0].tag)

        # Assert Message verb has media
        self.assertEquals(message_children[1].tag, 'Media',
                          "Message does not have a Media, instead found: %s" %
                          message_children[1].tag)

    def test_adopt_no_session(self):
        response = self.message('I want to adopt', url='/')

        root = ElementTree.fromstring(response.data)

        #Assert no session + I want to adopt will return a pet
        message_query = root.findall('Message')
        message_children = list(message_query[0])
        self.assertEquals(message_children[1].tag, 'Media',
                          "Message does not have Media when posting with no session: %s" %
                          message_children[1].tag
                          )

    def test_adopt_session(self):
        # Assert session + I want to adopt will return a shelter
        with self.test_app.session_transaction() as sess:
            sess['shelterId'] = 'AK58'
        response = self.test_app.post('/', data={'Body':'I want to adopt', 'From': '+15558675309'})
        root = ElementTree.fromstring(response.data)
        message_query = root.findall('Message')
        message_children = list(message_query[0])
        self.assertEquals(len(message_children),1,
                          "Message has more than one noun: %s" %
                          len(message_children)
                          )
        self.assertEquals(message_children[0].text, 'Shelter Info:\nphone number: \nemail: agsrescue@gmail.com\n',
                         "Message does not shelter info: %s" %
                         message_children[0].text
                         )