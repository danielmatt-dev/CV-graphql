from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model

from hacker_news.schema import schema
from language.models import Language

# Create your tests here.
GET_ALL_LANGUAGES = '''
query {
  languages {
    id
    language
  }
}
'''

GET_LANGUAGES_WITH_WILDCARD = '''
query {
  languages(search: "*") {
    id
    language
  }
}
'''

GET_FILTERED_LANGUAGES = '''
query GetFilteredLanguages($search: String!) {
  languages(search: $search) {
    id
    language
  }
}
'''

GET_LANGUAGE_BY_ID = '''
query GetLanguageById($idLanguage: Int!) {
  languageById(idLanguage: $idLanguage) {
    id
    language
  }
}
'''

CREATE_OR_UPDATE_LANGUAGE = '''
mutation CreateLanguage($idLanguage: Int, $language: String!) {
  createLanguage(idLanguage: $idLanguage, language: $language) {
    idLanguage
    language
    postedBy {
      username
    }
  }
}
'''

DELETE_LANGUAGE_MUTATION = '''
mutation DeleteLanguage($idLanguage: Int!) {
  deleteLanguage(idLanguage: $idLanguage) {
    idLanguage
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

class LanguageTestCase(GraphQLTestCase):
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
        self.language1 = mixer.blend(Language, posted_by=self.user)
        self.language2 = mixer.blend(Language, posted_by=self.user)

    def test_get_all_languages(self):
        # Realizar la consulta
        response = self.query(
            GET_ALL_LANGUAGES,
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response without filter:", content)  # Depuración

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar los idiomas devueltos
        languages = content['data']['languages']
        assert len(languages) == 2  # Los dos idiomas creados en el setUp
        assert any(language['id'] == str(self.language1.id) for language in languages)
        assert any(language['id'] == str(self.language2.id) for language in languages)

    def test_get_filtered_languages(self):
        # Cambiar el idioma para aplicar filtro
        self.language1.language = "English"
        self.language1.save()
        self.language2.language = "Spanish"
        self.language2.save()

        # Realizar la consulta con filtro
        response = self.query(
            GET_FILTERED_LANGUAGES,
            variables={"search": "English"},
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response with filter:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que solo se devuelve el idioma filtrado
        languages = content['data']['languages']
        assert len(languages) == 1
        assert languages[0]['id'] == str(self.language1.id)

    def test_get_languages_not_logged_in(self):
        # Realizar la consulta sin autenticación
        response = self.query(
            GET_ALL_LANGUAGES
        )
        content = json.loads(response.content)
        print("Response without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"

    def test_get_language_by_id(self):
        # Realizar la consulta para language1
        response = self.query(
            GET_LANGUAGE_BY_ID,
            variables={"idLanguage": self.language1.id},
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response for existing language:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el idioma devuelto coincide con language1
        language = content['data']['languageById']
        assert language['id'] == str(self.language1.id)
        assert language['language'] == self.language1.language

    def test_get_nonexistent_language_by_id(self):
        # Realizar la consulta para un ID que no existe
        response = self.query(
            GET_LANGUAGE_BY_ID,
            variables={"idLanguage": 9999},  # ID inexistente
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response for nonexistent language:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que no se devuelve ningún idioma
        language = content['data']['languageById']
        assert language is None

    def test_get_language_by_id_not_logged_in(self):
        # Realizar la consulta sin autenticación
        response = self.query(
            GET_LANGUAGE_BY_ID,
            variables={"idLanguage": self.language1.id}
        )
        content = json.loads(response.content)
        print("Response without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"

    def test_create_language_not_logged_in(self):
        # Realizar la mutación sin encabezados de autenticación
        response = self.query(
            CREATE_OR_UPDATE_LANGUAGE,
            variables={
                "idLanguage": None,  # Para crear un nuevo idioma
                "language": "Unauthorized Language"
            }
        )
        content = json.loads(response.content)
        print("Full response when not logged in:", content)  # Depuración

        # Validar que existe un error
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        print("Error message received: -- LANGUAGE NOT LOGGED", error_message)  # Imprime el mensaje exacto

        # Validar el mensaje específico
        assert 'Not logged in' in error_message  # Validación parcial para adaptarse a prefijos


    def test_create_language_with_valid_id(self):
        # Realizar la mutación para crear un idioma con un ID específico
        response = self.query(
            CREATE_OR_UPDATE_LANGUAGE,
            variables={
                "idLanguage": 0,  # Para crear un nuevo idioma
                "language": "English"
            },
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response for creating language with valid ID:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el idioma fue creado correctamente
        language = content['data']['createLanguage']
        assert language['language'] == "English"
        assert language['postedBy']['username'] == self.user.username

    def test_create_language_update(self):
        # Crear un idioma existente en la base de datos
        self.language1 = mixer.blend(
            Language,
            language="Old Language",
            posted_by=self.user
        )

        # Realizar la mutación para actualizar el idioma existente
        response = self.query(
            CREATE_OR_UPDATE_LANGUAGE,
            variables={
                "idLanguage": self.language1.id,
                "language": "Updated Language"
            },
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response when updating language:", content)  # Depuración

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el registro devuelto es correcto
        data = content['data']['createLanguage']
        assert data['idLanguage'] == self.language1.id
        assert data['language'] == "Updated Language"
        assert data['postedBy']['username'] == self.user.username

        # Obtener el registro actualizado en la base de datos
        language = Language.objects.get(id=self.language1.id)

        # Validar que los datos en la base de datos son correctos
        assert language.language == "Updated Language"
        assert language.posted_by == self.user

    def test_delete_language_existing(self):
        # Crear un idioma existente
        self.language1 = mixer.blend(
            Language,
            language="Test Language",
            posted_by=self.user
        )

        # Realizar la mutación para eliminar el idioma
        response = self.query(
            DELETE_LANGUAGE_MUTATION,
            variables={"idLanguage": self.language1.id},
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response when deleting existing language:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el idioma fue eliminado de la base de datos
        with self.assertRaises(Language.DoesNotExist):
            Language.objects.get(id=self.language1.id)


    def test_delete_language_nonexistent_id(self):
        # Realizar la mutación con un ID que no existe
        response = self.query(
            DELETE_LANGUAGE_MUTATION,
            variables={"idLanguage": 9999},  # ID inexistente
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response when deleting non-existent language:", content)

        # Validar que se lanza la excepción 'Invalid Language id!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Invalid Language id!"


    def test_delete_language_not_logged_in(self):
        # Crear un idioma existente
        self.language1 = mixer.blend(
            Language,
            language="Test Language",
            posted_by=self.user
        )

        # Realizar la mutación sin encabezado de autenticación
        response = self.query(
            DELETE_LANGUAGE_MUTATION,
            variables={"idLanguage": self.language1.id}  # Sin autenticación
        )
        content = json.loads(response.content)
        print("Response when deleting without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"





