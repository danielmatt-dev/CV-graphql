from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model
from datetime import date

from hacker_news.schema import schema
from education.models import Education

# Create your tests here.

EDUCATION_QUERY = '''
query EducationQuery($search: String) {
  degrees(search: $search) {
    id
    degree
    university
    startDate
    endDate
  }
}
'''

DEGREE_BY_ID_QUERY = '''
query DegreeById($idEducation: Int!) {
    degreeById(idEducation: $idEducation) {
        id
        degree
        university
    }
}
'''

CREATE_EDUCATION_MUTATION = '''
mutation CreateEducation($idEducation: Int, $degree: String!, $university: String!, $startDate: Date!, $endDate: Date!) {
    createEducation(idEducation: $idEducation, degree: $degree, university: $university, startDate: $startDate, endDate: $endDate) {
        idEducation
        degree
        university
        startDate
        endDate
        postedBy {
            username
        }
    }
}
'''

DELETE_EDUCATION_MUTATION = '''
mutation DeleteEducation($idEducation: Int!) {
    deleteEducation(idEducation: $idEducation) {
        idEducation
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

class EducationTestCase(GraphQLTestCase):
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
        self.education1 = mixer.blend(Education, posted_by=self.user)
        self.education2 = mixer.blend(Education, posted_by=self.user)

    def test_education_query_no_search(self):
        # Caso: Sin pasar 'search' (debería devolver todos los registros)
        response = self.query(
            '''
            query {
                degrees {
                    id
                    degree
                    university
                    startDate
                    endDate
                }
            }
            ''',
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Response without search:", content)  # Depuración

        # Validaciones
        self.assertResponseNoErrors(response)
        assert len(content['data']['degrees']) == 2  # Dos registros creados en el setUp

    def test_education_query_search_asterisk(self):
        # Caso: search="*" (devuelve los primeros 10 registros)
        response = self.query(
            '''
            query EducationQuery($search: String) {
                degrees(search: $search) {
                    id
                    degree
                    university
                    startDate
                    endDate
                }
            }
            ''',
            variables={"search": "*"},
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Response with search '*':", content)  # Depuración

        # Validaciones
        self.assertResponseNoErrors(response)

        # Verifica que devuelve hasta 10 registros
        assert len(content['data']['degrees']) <= 10

        # Verifica que incluye los registros creados en el setUp
        degrees = [degree['id'] for degree in content['data']['degrees']]
        assert str(self.education1.id) in degrees
        assert str(self.education2.id) in degrees

    def test_education_query_search_specific(self):
        # Actualiza uno de los registros para garantizar que coincida con el filtro
        self.education2.degree = "Master's in Data Science"
        self.education2.save()

        # Caso: search="Data" (filtra registros que contienen "Data" en el campo degree)
        response = self.query(
            '''
            query EducationQuery($search: String) {
                degrees(search: $search) {
                    id
                    degree
                    university
                    startDate
                    endDate
                }
            }
            ''',
            variables={"search": "Data"},
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Response with specific search:", content)  # Depuración

        # Validaciones
        self.assertResponseNoErrors(response)

        # Verifica que se devuelve exactamente 1 registro
        assert len(content['data']['degrees']) == 1

        # Verifica que el registro devuelto es el correcto
        assert content['data']['degrees'][0]['id'] == str(self.education2.id)
        assert content['data']['degrees'][0]['degree'] == "Master's in Data Science"

    def test_education_query_not_logged_in(self):
        # Caso: Usuario no autenticado intenta acceder al resolver
        response = self.query(
            '''
            query {
                degrees {
                    id
                    degree
                    university
                    startDate
                    endDate
                }
            }
            '''
        )
        content = json.loads(response.content)
        print("Response when not logged in:", content)  # Depuración

        # Validar que se lanza el error correspondiente
        assert 'errors' in content
        assert content['errors'][0]['message'] == 'Not logged in!'

    def test_resolve_degree_by_id_not_logged_in(self):
        # Realizar la consulta sin encabezados de autenticación
        response = self.query(
            DEGREE_BY_ID_QUERY,
            variables={"idEducation": 1}  # ID arbitrario
        )
        content = json.loads(response.content)
        print("Response when not logged in:", content)  # Depuración

        # Validar que se lanza el error de autenticación
        assert 'errors' in content
        assert content['errors'][0]['message'] == 'Not logged in!'

    def test_resolve_degree_by_id_valid(self):
        # Asociar el registro a un usuario
        self.education1.posted_by = self.user
        self.education1.save()

        # Realizar la consulta con un ID válido
        response = self.query(
            DEGREE_BY_ID_QUERY,
            variables={"idEducation": self.education1.id},
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Response with valid ID:", content)  # Depuración

        # Validar que se devuelve el registro correcto
        self.assertResponseNoErrors(response)
        assert content['data']['degreeById']['id'] == str(self.education1.id)
        assert content['data']['degreeById']['degree'] == self.education1.degree
        assert content['data']['degreeById']['university'] == self.education1.university

    def test_resolve_degree_by_id_invalid(self):
        # Realizar la consulta con un ID que no pertenece al usuario
        response = self.query(
            DEGREE_BY_ID_QUERY,
            variables={"idEducation": 999},  # ID arbitrario que no existe
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Response with invalid ID:", content)  # Depuración

        # Validar que no se devuelve ningún registro
        self.assertResponseNoErrors(response)
        assert content['data']['degreeById'] is None

    def test_create_education_not_logged_in(self):
        # Realizar la mutación sin encabezados de autenticación
        response = self.query(
            CREATE_EDUCATION_MUTATION,
            variables={
                "idEducation": None,
                "degree": "Bachelor's in Computer Science",
                "university": "Test University",
                "startDate": "2020-01-01",
                "endDate": "2024-01-01"
            }
        )
        content = json.loads(response.content)
        print("Full response when not logged in:", content)  # Depuración

        # Validar que existe un error
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        print("Error message received:", error_message)  # Imprime el mensaje exacto

        # Validar el mensaje específico
        assert 'Not logged in' in error_message  # Validación parcial para adaptarse a prefijos

    def test_create_education_new(self):
        # Realizar la mutación para crear un nuevo registro
        response = self.query(
            CREATE_EDUCATION_MUTATION,
            variables={
                "idEducation": None,
                "degree": "Bachelor's in Computer Science",
                "university": "Test University",
                "startDate": "2020-01-01",
                "endDate": "2024-01-01"
            },
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Response when creating new education:", content)  # Depuración

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el registro devuelto es correcto
        data = content['data']['createEducation']
        assert data['degree'] == "Bachelor's in Computer Science"
        assert data['university'] == "Test University"
        assert data['startDate'] == "2020-01-01"
        assert data['endDate'] == "2024-01-01"
        assert data['postedBy']['username'] == self.user.username

        # Obtener el registro creado en la base de datos
        education = Education.objects.get(id=data['idEducation'])

        # Depuración: Imprimir valores de fechas
        print("Database start_date:", education.start_date)
        print("Database end_date:", education.end_date)

        # Convertir las fechas de la base de datos a `date` antes de la comparación
        assert education.start_date.date() == date(2020, 1, 1)  # Convertir a `date`
        assert education.end_date.date() == date(2024, 1, 1)
        assert education.degree == "Bachelor's in Computer Science"
        assert education.university == "Test University"
        assert education.posted_by == self.user

    def test_create_education_update(self):
        # Crear un registro existente en la base de datos
        self.education1 = mixer.blend(
            Education,
            degree="Old Degree",
            university="Old University",
            start_date="2015-01-01",
            end_date="2019-01-01",
            posted_by=self.user
        )

        # Realizar la mutación para actualizar el registro existente
        response = self.query(
            CREATE_EDUCATION_MUTATION,
            variables={
                "idEducation": self.education1.id,
                "degree": "Master's in Data Science",
                "university": "Updated University",
                "startDate": "2021-01-01",
                "endDate": "2023-01-01"
            },
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response when updating education:", content)  # Depuración

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el registro devuelto es correcto
        data = content['data']['createEducation']
        assert data['idEducation'] == self.education1.id
        assert data['degree'] == "Master's in Data Science"
        assert data['university'] == "Updated University"
        assert data['startDate'] == "2021-01-01"
        assert data['endDate'] == "2023-01-01"
        assert data['postedBy']['username'] == self.user.username

        # Obtener el registro actualizado en la base de datos
        education = Education.objects.get(id=self.education1.id)

        # Validar que los datos en la base de datos son correctos
        assert education.degree == "Master's in Data Science"
        assert education.university == "Updated University"
        assert education.start_date.date() == date(2021, 1, 1)  # Convertir a `date`
        assert education.end_date.date() == date(2023, 1, 1)
        assert education.posted_by == self.user

    def test_delete_education_existing(self):
        # Crear un registro existente
        self.education1 = mixer.blend(
            Education,
            degree="Test Degree",
            university="Test University",
            start_date="2015-01-01",
            end_date="2019-01-01",
            posted_by=self.user
        )

        # Realizar la mutación para eliminar el registro
        response = self.query(
            DELETE_EDUCATION_MUTATION,
            variables={"idEducation": self.education1.id},
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response when deleting existing education:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el registro fue eliminado de la base de datos
        with self.assertRaises(Education.DoesNotExist):
            Education.objects.get(id=self.education1.id)

    def test_delete_education_nonexistent_id(self):
        # Realizar la mutación con un ID que no existe
        response = self.query(
            DELETE_EDUCATION_MUTATION,
            variables={"idEducation": 9999},  # ID inexistente
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response when deleting non-existent education:", content)

        # Validar que se lanza la excepción 'Invalid Education id!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Invalid Education id!"

    def test_delete_education_not_logged_in(self):
        # Crear un registro existente
        self.education1 = mixer.blend(
            Education,
            degree="Test Degree",
            university="Test University",
            start_date="2015-01-01",
            end_date="2019-01-01",
            posted_by=self.user
        )

        # Realizar la mutación sin encabezado de autenticación
        response = self.query(
            DELETE_EDUCATION_MUTATION,
            variables={"idEducation": self.education1.id}  # Sin autenticación
        )
        content = json.loads(response.content)
        print("Response when deleting without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"

    



















