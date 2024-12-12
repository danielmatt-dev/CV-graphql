from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model

from hacker_news.schema import schema
from archivements.models import Archivements

# Create your tests here.

GET_ALL_ARCHIVEMENTS = '''
query {
  archivements(search: "*") {
    id
    archivementName
    year
  }
}
'''

GET_FILTERED_ARCHIVEMENTS = '''
query ($search: String!) {
  archivements(search: $search) {
    id
    archivementName
    year
  }
}
'''

GET_ARCHIVEMENT_BY_ID = '''
query ($idArchivement: Int!){
  archivementsById(idArchivement: $idArchivement){
    id
    archivementName
    year
  }
}
'''

CREATE_OR_UPDATE_ARCHIVEMENTS = '''
mutation ($idArchivement: Int!, $archivementName: String!, $year: Int!) {
  createArchivement(idArchivement: $idArchivement, archivementName: $archivementName, year: $year) {
    idArchivement
    archivementName
    year
    postedBy {
      username
    }
  }
}
'''

DELETE_ARCHIVEMENT = '''
mutation ($idArchivement: Int!) {
  deleteArchivement(idArchivement: $idArchivement) {
    idArchivement
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

class ArchivementTestCase(GraphQLTestCase):
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
        self.archivement1 = mixer.blend(Archivements, posted_by=self.user)
        self.archivement2 = mixer.blend(Archivements, posted_by=self.user)

    def test_get_all_archivement(self):
        response = self.query(
            GET_ALL_ARCHIVEMENTS,
            headers=self.headers,
        )
        content = json.loads(response.content)
        print("Response without filter:", content)

        self.assertResponseNoErrors(response)

        archivements = content['data']['archivements']
        assert len(archivements) == 2
        assert any(archivement['id'] == str(self.archivement1.id) for archivement in archivements)
        assert any(archivement['id'] == str(self.archivement2.id) for archivement in archivements)

    def test_get_filtered_archivements(self):
        self.archivement1.archivementName = "Ganar"
        self.archivement1.save()
        self.archivement2.archivementName = "Triunfar"
        self.archivement2.save()

        response = self.query(
            GET_FILTERED_ARCHIVEMENTS,
            variables={"search": "Ganar"},
            headers=self.headers,
        )
        content = json.loads(response.content)
        print("Response with filter:", content)

        self.assertResponseNoErrors(response)

        archivements = content['data']['archivements']
        assert len(archivements) == 1
        assert archivements[0]["id"] == str(self.archivement1.id)

    def test_get_archivements_not_logged_in(self):
        response = self.query(
            GET_ALL_ARCHIVEMENTS
        )
        content = json.loads(response.content)
        print("Response without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"

    def test_get_archivement_by_id(self):
        response = self.query(
            GET_ARCHIVEMENT_BY_ID,
            variables={"idArchivement": self.archivement1.id},
            headers=self.headers,
        )
        content = json.loads(response.content)
        print("Responde for existing archivement", content)

        self.assertResponseNoErrors(response)

        archivement = content['data']['archivementsById']
        assert archivement['id'] == str(self.archivement1.id)
        assert archivement['archivementName'] == self.archivement1.archivementName

    def test_get_archivement_by_id_not_logged_in(self):
        response = self.query(
            GET_ARCHIVEMENT_BY_ID,
            variables={"idArchivement": self.archivement1.id},
        )
        content = json.loads(response.content)
        print("REsponse without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"

    def test_create_archivement_not_logged_in(self):
        response = self.query(
            CREATE_OR_UPDATE_ARCHIVEMENTS,
            variables={
                "idArchivement": 0,
                "archivementName": "Unauthorized archivement",
                "year": 2020
            }
        )
        content = json.loads(response.content)
        print("Full response when not logged in:", content)

        assert 'errors' in content
        error_message = content['errors'][0]['message']
        print("Error message received: -- ARCHIVEMENT NOT LOGGED", error_message)  # Imprime el mensaje exacto

        # Validar el mensaje específico
        assert 'Not logged in' in error_message  # Validación parcial para adaptarse a prefijos


    def test_create_archivement_negative_year(self):
        response = self.query(
            CREATE_OR_UPDATE_ARCHIVEMENTS,
            variables={
                "idArchivement": 0,
                "archivementName": "Unauthorized archivement",
                "year": -1
            },
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Full response when not logged in:", content)

        assert 'errors' in content
        error_message = content['errors'][0]['message']
        print("Error message received: -- ARCHIVEMENT NOT LOGGED", error_message)  # Imprime el mensaje exacto

        # Validar el mensaje específico
        assert 'The year must be positive' in error_message  # Validación parcial para adaptarse a prefijos

    def test_create_archivement_with_valid_id(self):
        response = self.query(
            CREATE_OR_UPDATE_ARCHIVEMENTS,
            variables={
                "idArchivement": 0,
                "archivementName": "Lograr",
                "year": 2024
            },
            headers=self.headers,
        )
        content = json.loads(response.content)
        print("Response for creating archivement with valid ID:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el archivement fue creado correctamente
        archivement = content['data']['createArchivement']
        assert archivement['archivementName'] == "Lograr"
        assert archivement['year'] == 2024
        assert archivement['postedBy']['username'] == self.user.username

    def test_create_archivement_update(self):
        self.archivement1 = mixer.blend(
            Archivements,
            archivementName="Old archivement",
            year=2020,
            posted_by=self.user
        )

        response = self.query(
            CREATE_OR_UPDATE_ARCHIVEMENTS,
            variables={
                "idArchivement": self.archivement1.id,
                "archivementName": "Updated Archivement",
                "year": 2024
            },
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Response when updating archivement:", content)  # Depuración

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el registro devuelto es correcto
        data = content['data']['createArchivement']
        assert data['idArchivement'] == self.archivement1.id 
        assert data['archivementName'] == "Updated Archivement"
        assert data['year'] == 2024
        assert data['postedBy']['username'] == self.user.username

        # Obtener el registro actualizado en la base de datos
        archivement = Archivements.objects.get(id=self.archivement1.id)

        # Validar que los datos en la base de datos son correctos
        assert archivement.archivementName == "Updated Archivement"
        assert archivement.year == 2024
        assert archivement.posted_by == self.user

    def test_delete_archivement_existing(self):
        response = self.query(
            DELETE_ARCHIVEMENT,
            variables={"idArchivement": self.archivement1.id},
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Response when deleting existing archivement:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el archivement fue eliminado de la base de datos
        with self.assertRaises(Archivements.DoesNotExist):
            Archivements.objects.get(id=self.archivement1.id)

    def test_delete_archivement_nonexistent_id(self):
        response = self.query(
            DELETE_ARCHIVEMENT,
            variables={"idArchivement": 9999},
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Response when deleting non-existent archivement:", content)

        # Validar que se lanza la excepción 'Invalid Archivement id!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Invalid Archivement id!"

    def test_delete_archivement_not_logged_in(self):
        response = self.query(
            DELETE_ARCHIVEMENT,
            variables={"idArchivement": self.archivement1.id}
        )
        content = json.loads(response.content)
        print("Response when deleting without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"