from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model

from hacker_news.schema import schema
from links.models import Link

# Create your tests here.

LINKS_QUERY = '''
 {
   links {
     id
     url
     description
   }
 }
'''

USERS_QUERY = '''
 {
   users {
     id
     username
     password
   }
 }
'''

VOTES_QUERY = '''
{
  votes{
    id
    link {
      id
      url
      description
    }
  }
}
'''

CREATE_LINK_MUTATION = '''
 mutation createLinkMutation($url: String!, $description: String!) {
     createLink(url: $url, description: $description) {
         description
     }
 }
'''

CREATE_USER_MUTATION = '''
 mutation createUserMutation($email: String!, $password: String!, $username: String!) {
     createUser(email: $email, password: $password, username: $username) {
         user {
            username
            password
         }
     }
 }
'''

LOGIN_USER_MUTATION = '''
 mutation TokenAuthMutation($username: String!, $password: String!) {
     tokenAuth(username: $username, password: $password) {
        token
     }
 }
'''

CREATE_VOTE_MUTATION = '''
 mutation createVoteMutation($linkId: Int!) {
     createVote(linkId: $linkId) {
         user {
             id
             username
         }
         link {
             id
             url
         }
     }
 }
'''

class LinkTestCase(GraphQLTestCase):
    GRAPHQL_URL = "http://localhost:8000/graphql/"
    GRAPHQL_SCHEMA = schema
    
    def setUp(self):
        self.link1 = mixer.blend(Link)
        self.link2 = mixer.blend(Link)
   
        response_user = self.query(
            CREATE_USER_MUTATION,
            variables={'email': 'adsoft@live.com.mx', 'username': 'adsoft', 'password': 'adsoft'}
        )
        print('user mutation ')
        content_user = json.loads(response_user.content)
        print(content_user['data'])

        response_token = self.query(
            LOGIN_USER_MUTATION,
            variables={'username': 'adsoft', 'password': 'adsoft'}
        )

        content_token = json.loads(response_token.content)
        token = content_token['data']['tokenAuth']['token']
        print(token)
        self.headers = {"AUTHORIZATION": f"JWT {token}"}


    def test_links_query(self):
        response = self.query(
            LINKS_QUERY,
        )
        print(response)
        content = json.loads(response.content)
        print(response.content)
        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)
        print ("query link results ")
        print (response)
        assert len(content['data']['links']) == 2


    def test_users_query(self):
        response = self.query(
            USERS_QUERY,
        )
        print(response)
        content = json.loads(response.content)
        print(response.content)
        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)
        print ("query users results ")
        print (response)
        assert len(content['data']['users']) == 3


    def test_createLink_mutation(self):
        response = self.query(
            CREATE_LINK_MUTATION,
            variables={'url': 'https://google.com', 'description': 'google'},
            headers=self.headers
        )
        content = json.loads(response.content)
        print(content['data'])
        self.assertResponseNoErrors(response)
        self.assertDictEqual({"createLink": {"description": "google"}}, content['data']) 

    def test_createVote_mutation(self):
        response = self.query(
            CREATE_VOTE_MUTATION,
            variables={'linkId': self.link1.id},
            headers=self.headers
        )
        
        content = json.loads(response.content)
        print(content)
        
        self.assertResponseNoErrors(response)
        assert content['data']['createVote']['link']['id'] == str(self.link1.id)
        assert content['data']['createVote']['link']['url'] == self.link1.url
        assert content['data']['createVote']['user']['username'] == 'adsoft'

    def test_createVote_unauthenticated(self):
        response = self.query(
            CREATE_VOTE_MUTATION,
            variables={'linkId': self.link1.id},
            headers={}
        )
        content = json.loads(response.content)
        print(content)

        assert 'errors' in content
        assert content['errors'][0]['message'] == 'GraphQLError: You must be logged to vote!'

    def test_createVote_invalid_link(self):
        response = self.query(
            CREATE_VOTE_MUTATION,
            variables={'linkId': 9999},
            headers=self.headers
        )
        content = json.loads(response.content)
        print(content)

        assert 'errors' in content
        assert content['errors'][0]['message'] == 'Invalid Link!'

    def test_votes_query(self):
        # Crear un voto para el enlace `link1` utilizando la mutación `CREATE_VOTE_MUTATION`
        response_vote = self.query(
            CREATE_VOTE_MUTATION,
            variables={'linkId': self.link1.id},
            headers=self.headers  # Incluye la autenticación
        )

        # Depura la respuesta de la mutación
        content_vote = json.loads(response_vote.content)
        print("Vote Mutation Response:", content_vote)

        # Verifica que la mutación no devolvió errores
        self.assertResponseNoErrors(response_vote)

        # Realiza la consulta de votos utilizando `VOTES_QUERY`
        response = self.query(
            VOTES_QUERY,
            headers=self.headers  # Incluye la autenticación
        )

        # Convierte la respuesta de la consulta en un formato JSON manejable
        content = json.loads(response.content)
        print("Votes Query Response:", content)

        # Valida que no haya errores en la respuesta
        self.assertResponseNoErrors(response)

        # Verifica que hay exactamente 1 voto en la respuesta
        assert len(content['data']['votes']) == 1

        # Verifica que los datos del voto corresponden al enlace `link1` y al usuario `adsoft`
        vote = content['data']['votes'][0]
        assert vote['link']['id'] == str(self.link1.id)
        assert vote['link']['url'] == self.link1.url
        assert vote['link']['description'] == self.link1.description
