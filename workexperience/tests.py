from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model

from hacker_news.schema import schema
from workexperience.models import WorkExperience

# Create your tests here.

GET_ALL_WORK_EXPERIENCES = '''
query{
  workExperiences(search: "*") {
    id
    position
    company
    startDate
    endDate
    location
    archivements{
      id
      description
    }
  }
}
'''

GET_FILTERED_WORK_EXPERIENCES = '''
query ($search: String!) {
  workExperiences(search: $search) {
    id
    position
    company
    startDate
    endDate
    location
    archivements{
      id
      description
    }
  }
}
'''

GET_WORK_EXPERIENCE_BY_ID = '''
query ($idWork: Int!) {
  workExperiencebyid(idWork: $idWork) {
    id
    position
    company
    startDate
    endDate
    location
    archivements{
      id
      description
    }
  }
}
'''

CREATE_OR_UPDATE_WORK_EXPERIENCE = '''
mutation ($idWork: Int!, $position: String!, $company: String!, $startDate: Date!, $endDate: Date!, $location: String!, $archivements: [String!]!) {
  createWorkExperience(
    idWork: $idWork, 
    position: $position, 
    company: $company, 
    startDate: $startDate, 
    endDate: $endDate, 
    location: $location,
    archivements: $archivements
  ) {
    idWork
    position
    company
    startDate
    endDate
    location
    archivements
    postedBy{
        username
    }
  }
}
'''

DELETE_WORK_EXPERIENCE = '''
mutation ($idWork: Int!) {
  deleteWorkExperience(idWork: $idWork){
    idWork
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

class WorkExperienceTestCase(GraphQLTestCase):
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
        self.workExperience1 = mixer.blend(WorkExperience, posted_by=self.user)
        self.workExperience2 = mixer.blend(WorkExperience, posted_by=self.user)

    def test_get_all_work_experiences(self):
        response = self.query(
            GET_ALL_WORK_EXPERIENCES,
            headers=self.headers,
        )
        content = json.loads(response.content)
        print("Response without filter:", content)

        self.assertResponseNoErrors(response)

        workExperiences = content['data']['workExperiences']
        assert len(workExperiences) == 2
        assert any(workExperience['id'] == str(self.workExperience1.id) for workExperience in workExperiences)
        assert any(workExperience['id'] == str(self.workExperience2.id) for workExperience in workExperiences)
    
    def test_get_filtered_work_experiences(self):
        self.workExperience1.position = "Programador"
        self.workExperience1.save()

        response = self.query(
            GET_FILTERED_WORK_EXPERIENCES,
            variables={"search": "Programador"},
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Response with filter:", content)

        self.assertResponseNoErrors(response)

        workExperiences = content['data']['workExperiences']
        assert len(workExperiences) == 1
        assert workExperiences[0]["id"] == str(self.workExperience1.id)

    def test_get_all_work_experiences_not_logged_in(self):
        response = self.query(
            GET_ALL_WORK_EXPERIENCES
        )
        content = json.loads(response.content)
        print("Response without authentication:", content)

         # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"

    def test_get_work_experience_by_id(self):
        response = self.query(
            GET_WORK_EXPERIENCE_BY_ID,
            variables={"idWork": self.workExperience1.id},
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Responde for existing archivement", content)

        self.assertResponseNoErrors(response)

        workExperience = content['data']['workExperiencebyid']
        assert workExperience['id'] == str(self.workExperience1.id)
        assert workExperience['position'] == self.workExperience1.position

    def test_get_work_experience_not_logged_in(self):
        response = self.query(
            GET_WORK_EXPERIENCE_BY_ID,
            variables={"idWork": self.workExperience1.id},
        )
        content = json.loads(response.content)
        print("REsponse without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"

    def test_create_work_experience_not_logged_in(self):
        response = self.query(
            CREATE_OR_UPDATE_WORK_EXPERIENCE,
            variables={
                "idWork": 0,
                "position": "Software Developer",
                "company": "TechCorp",
                "startDate": "2023-01-01",
                "endDate": "2023-12-31",
                "location": "Remote",
                "archivements": [
                    "Implemented CI/CD pipeline",
                    "Reduced system downtime by 20%"
                ]
            }
        )
        content = json.loads(response.content)
        print("Full response when not logged in:", content)

        assert 'errors' in content
        error_message = content['errors'][0]['message']
        print("Error message received: -- WORK_EXPERIENCE NOT LOGGED", error_message)

        # Validar el mensaje específico
        assert "Not logged in" in error_message

    def test_create_work_experience_with_valid_id(self):
        response = self.query(
            CREATE_OR_UPDATE_WORK_EXPERIENCE,
            variables={
                "idWork": 0,
                "position": "Software Developer",
                "company": "TechCorp",
                "startDate": "2023-01-01",
                "endDate": "2023-12-31",
                "location": "Remote",
                "archivements": [
                    "Implemented CI/CD pipeline",
                    "Reduced system downtime by 20%"
                ]
            },
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Response for creating workExperience with valid ID:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        workExperience = content['data']['createWorkExperience']
        assert workExperience['position'] == "Software Developer"
        assert workExperience['company'] == "TechCorp"
        assert workExperience['startDate'] == "2023-01-01"
        assert workExperience['endDate'] == "2023-12-31"
        assert workExperience['location'] == "Remote"

    def test_update_work_experience(self):
        response = self.query(
            CREATE_OR_UPDATE_WORK_EXPERIENCE,
            variables={
                "idWork": self.workExperience1.id,
                "position": "Updated position",
                "company": "Updated company",
                "startDate": "2024-01-01",
                "endDate": "2024-12-31",
                "location": "Updated location",
                "archivements": [
                    "Logro 1",
                    "Logro 2"
                ]
            },
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Response when updating workExperience:", content)  # Depuración

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el registro devuelto es correcto
        data = content['data']['createWorkExperience']
        assert data['idWork'] == self.workExperience1.id
        assert data['position'] == "Updated position"
        assert data['company'] == "Updated company"
        assert data['startDate'] == "2024-01-01"
        assert data['endDate'] == "2024-12-31"
        assert data['location'] == "Updated location"
        assert data['postedBy']['username'] == self.user.username

        # Obtener el registro actualizado en la base de datos
        workExperience = WorkExperience.objects.get(id=self.workExperience1.id)

        # Validar que los datos en la base de datos son correctos
        assert workExperience.position == "Updated position"
        assert workExperience.company == "Updated company"
        assert workExperience.start_date.strftime("%Y-%m-%d") == "2024-01-01"
        assert workExperience.end_date.strftime("%Y-%m-%d") == "2024-12-31"
        assert workExperience.location == "Updated location"
        assert workExperience.posted_by == self.user

    def test_delete_work_experience(self):
        response = self.query(
            DELETE_WORK_EXPERIENCE,
            variables={"idWork": self.workExperience1.id},
            headers=self.headers,
        )
        content = json.loads(response.content)
        print("Response when deleting existing archivement:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        #Validar que el archivement fue eliminado de la base de datos
        with self.assertRaises(WorkExperience.DoesNotExist):
            WorkExperience.objects.get(id=self.workExperience1.id)

    def test_delete_work_experience_nonexistent_id(self):
        response = self.query(
            DELETE_WORK_EXPERIENCE,
            variables={"idWork": 9999},
            headers=self.headers,
        )
        content = json.loads(response.content)
        print("Response when deleting non-existent archivement:", content)

        # Validar que se lanza la excepción 'Invalid WorkExperience id!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Invalid WorkExperience id!"

    def test_delete_work_experience_not_logged_in(self):
        response = self.query(
            DELETE_WORK_EXPERIENCE,
            variables={"idWork": self.workExperience1.id},
        )
        content = json.loads(response.content)
        print("Response when deleting without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"

    