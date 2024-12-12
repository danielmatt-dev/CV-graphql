from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model

from hacker_news.schema import schema
from interest.models import Interest

# Create your tests here.

GET_ALL_INTERESTS = '''
query {
  interest {
    id
    name
  }
}
'''

GET_INTERESTS_WITH_WILDCARD = '''
query {
  interest(search: "*") {
    id
    name
  }
}
'''

GET_FILTERED_INTERESTS = '''
query GetFilteredInterests($search: String!) {
  interest(search: $search) {
    id
    name
  }
}
'''

GET_INTEREST_BY_ID = '''
query GetInterestById($idInterest: Int!) {
  interestById(idInterest: $idInterest) {
    id
    name
  }
}
'''

CREATE_OR_UPDATE_INTEREST = '''
mutation CreateInterest($idInterest: Int, $name: String!) {
  createInterest(idInterest: $idInterest, name: $name) {
    idInterest
    name
    postedBy {
      username
    }
  }
}
'''

DELETE_INTEREST_MUTATION = '''
mutation DeleteInterest($idInterest: Int!) {
  deleteInterest(idInterest: $idInterest) {
    idInterest
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

class InterestTestCase(GraphQLTestCase):
    GRAPHQL_URL = "http://localhost:8000/graphql/"
    GRAPHQL_SCHEMA = schema

    def setUp(self):
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

        # Crear usuario y asociar registros
        self.user = get_user_model().objects.get(username="adsoft")
        self.interest1 = mixer.blend(Interest, posted_by=self.user)
        self.interest2 = mixer.blend(Interest, posted_by=self.user)

    def test_get_all_interests(self):
        # Realizar la consulta
        response = self.query(
            GET_ALL_INTERESTS,
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response without filter:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar los intereses devueltos
        interest = content['data']['interest']
        assert len(interest) == 2  # Los dos intereses creados en el setUp
        assert any(interest['id'] == str(self.interest1.id) for interest in interest)
        assert any(interest['id'] == str(self.interest2.id) for interest in interest)

    def test_get_filtered_interests(self):
        # Cambiar el nombre de los intereses para filtrar
        self.interest1.name = "Programming"
        self.interest1.save()
        self.interest2.name = "Reading"
        self.interest2.save()

        # Realizar la consulta con filtro
        response = self.query(
            GET_FILTERED_INTERESTS,
            variables={"search": "Programming"},
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response with filter:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que solo se devuelve el interés filtrado
        interests = content['data']['interest']
        assert len(interests) == 1
        assert interests[0]['id'] == str(self.interest1.id)

    def test_get_interests_not_logged_in(self):
        # Realizar la consulta sin autenticación
        response = self.query(
            GET_ALL_INTERESTS
        )
        content = json.loads(response.content)
        print("Response without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"
    
    def test_get_interest_by_id(self):
        # Realizar la consulta para interest1
        response = self.query(
            GET_INTEREST_BY_ID,
            variables={"idInterest": self.interest1.id},
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response for existing interest:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el interés devuelto coincide con interest1
        interest = content['data']['interestById']
        assert interest['id'] == str(self.interest1.id)
        assert interest['name'] == self.interest1.name

    def test_get_nonexistent_interest_by_id(self):
        # Realizar la consulta para un ID que no existe
        response = self.query(
            GET_INTEREST_BY_ID,
            variables={"idInterest": 9999},  # ID inexistente
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response for nonexistent interest:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que no se devuelve ningún interés
        interest = content['data']['interestById']
        assert interest is None

    def test_get_interest_by_id_not_logged_in(self):
        # Realizar la consulta sin autenticación
        response = self.query(
            GET_INTEREST_BY_ID,
            variables={"idInterest": self.interest1.id}
        )
        content = json.loads(response.content)
        print("Response without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"

    def test_create_interest_not_logged_in(self):
        # Realizar la mutación sin encabezados de autenticación
        response = self.query(
            CREATE_OR_UPDATE_INTEREST,
            variables={
                "idInterest": None,  # Para crear un nuevo interés
                "name": "Unauthorized Interest"
            }
        )
        content = json.loads(response.content)
        print("Full response when not logged in:", content)  # Depuración

        # Validar que existe un error
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        print("Error message received: -- INTEREST NOT LOOGED", error_message)  # Imprime el mensaje exacto

        # Validar el mensaje específico
        assert 'Not logged in' in error_message  # Validación parcial para adaptarse a prefijos

    def test_create_interest_with_valid_id(self):
        # Realizar la mutación para crear un interés con un ID específico
        response = self.query(
            CREATE_OR_UPDATE_INTEREST,
            variables={
                "idInterest": 0,  # Para crear un nuevo interés
                "name": "Programming"
            },
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response for creating interest with valid ID:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el interés fue creado correctamente
        interest = content['data']['createInterest']
        assert interest['name'] == "Programming"
        assert interest['postedBy']['username'] == self.user.username

    def test_create_interest_update(self):
        # Crear un interés existente en la base de datos
        self.interest1 = mixer.blend(
            Interest,
            name="Old Interest",
            posted_by=self.user
        )

        # Realizar la mutación para actualizar el interés existente
        response = self.query(
            CREATE_OR_UPDATE_INTEREST,
            variables={
                "idInterest": self.interest1.id,
                "name": "Updated Interest"
            },
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response when updating interest:", content)  # Depuración

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el registro devuelto es correcto
        data = content['data']['createInterest']
        assert data['idInterest'] == self.interest1.id
        assert data['name'] == "Updated Interest"
        assert data['postedBy']['username'] == self.user.username

        # Obtener el registro actualizado en la base de datos
        interest = Interest.objects.get(id=self.interest1.id)

        # Validar que los datos en la base de datos son correctos
        assert interest.name == "Updated Interest"
        assert interest.posted_by == self.user


    def test_delete_interest_existing(self):
        # Crear un interés existente
        self.interest1 = mixer.blend(
            Interest,
            name="Test Interest",
            posted_by=self.user
        )

        # Realizar la mutación para eliminar el interés
        response = self.query(
            DELETE_INTEREST_MUTATION,
            variables={"idInterest": self.interest1.id},
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response when deleting existing interest:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el interés fue eliminado de la base de datos
        with self.assertRaises(Interest.DoesNotExist):
            Interest.objects.get(id=self.interest1.id)

    def test_delete_interest_nonexistent_id(self):
        # Realizar la mutación con un ID que no existe
        response = self.query(
            DELETE_INTEREST_MUTATION,
            variables={"idInterest": 9999},  # ID inexistente
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response when deleting non-existent interest:", content)

        # Validar que se lanza la excepción 'Invalid Interest id!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Invalid Interest id!"

    def test_delete_interest_not_logged_in(self):
        # Crear un interés existente
        self.interest1 = mixer.blend(
            Interest,
            name="Test Interest",
            posted_by=self.user
        )

        # Realizar la mutación sin encabezado de autenticación
        response = self.query(
            DELETE_INTEREST_MUTATION,
            variables={"idInterest": self.interest1.id}  # Sin autenticación
        )
        content = json.loads(response.content)
        print("Response when deleting without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"





