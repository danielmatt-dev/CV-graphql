from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model

from hacker_news.schema import schema
from skills.models import Skill

# Create your tests here.

GET_ALL_SKILLS = '''
query {
  skill {
    id
    skill
  }
}
'''

GET_SKILLS_WITH_WILDCARD = '''
query {
  skill(search: "*") {
    id
    skill
  }
}
'''

GET_FILTERED_SKILLS = '''
query GetFilteredSkills($search: String!) {
  skill(search: $search) {
    id
    skill
  }
}
'''

GET_SKILL_BY_ID = '''
query GetSkillById($idSkill: Int!) {
  skillById(idSkill: $idSkill) {
    id
    skill
  }
}
'''

CREATE_OR_UPDATE_SKILL = '''
mutation CreateSkill($idSkill: Int, $skill: String!, $percent: Int!) {
  createSkill(idSkill: $idSkill, skill: $skill, percent: $percent) {
    idSkill
    skill
    percent
    postedBy {
      username
    }
  }
}
'''

DELETE_SKILL_MUTATION = '''
mutation DeleteSkill($idSkill: Int!) {
  deleteSkill(idSkill: $idSkill) {
    idSkill
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
        self.skill1 = mixer.blend(Skill, posted_by=self.user)
        self.skill2 = mixer.blend(Skill, posted_by=self.user)

    def test_get_all_skills(self):
        # Realizar la consulta
        response = self.query(
            GET_ALL_SKILLS,
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response without filter:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar las habilidades devueltas
        skills = content['data']['skill']
        assert len(skills) == 2  # Las dos habilidades creadas en el setUp
        assert any(skill['id'] == str(self.skill1.id) for skill in skills)
        assert any(skill['id'] == str(self.skill2.id) for skill in skills)

    def test_get_filtered_skills(self):
        # Cambiar el nombre de las habilidades para filtrar
        self.skill1.skill = "Programming"
        self.skill1.save()
        self.skill2.skill = "Reading"
        self.skill2.save()

        # Realizar la consulta con filtro
        response = self.query(
            GET_FILTERED_SKILLS,
            variables={"search": "Programming"},
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response with filter:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que solo se devuelve la habilidad filtrada
        skills = content['data']['skill']
        assert len(skills) == 1
        assert skills[0]['id'] == str(self.skill1.id)

    def test_get_skills_not_logged_in(self):
        # Realizar la consulta sin autenticación
        response = self.query(
            GET_ALL_SKILLS
        )
        content = json.loads(response.content)
        print("Response without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"

    def test_get_skill_by_id(self):
        # Realizar la consulta para skill1
        response = self.query(
            GET_SKILL_BY_ID,
            variables={"idSkill": self.skill1.id},
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response for existing skill:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que la habilidad devuelta coincide con skill1
        skill = content['data']['skillById']
        assert skill['id'] == str(self.skill1.id)
        assert skill['skill'] == self.skill1.skill

    def test_get_nonexistent_skill_by_id(self):
        # Realizar la consulta para un ID que no existe
        response = self.query(
            GET_SKILL_BY_ID,
            variables={"idSkill": 9999},  # ID inexistente
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response for nonexistent skill:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que no se devuelve ninguna habilidad
        skill = content['data']['skillById']
        assert skill is None

    def test_get_skill_by_id_not_logged_in(self):
        # Realizar la consulta sin autenticación
        response = self.query(
            GET_SKILL_BY_ID,
            variables={"idSkill": self.skill1.id}
        )
        content = json.loads(response.content)
        print("Response without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"

    def test_create_skill_not_logged_in(self):
        # Realizar la mutación sin encabezados de autenticación
        response = self.query(
            CREATE_OR_UPDATE_SKILL,
            variables={
                "idSkill": None,  # Para crear una nueva habilidad
                "skill": "Unauthorized Skill",
                "percent": 10
            }
        )
        content = json.loads(response.content)
        print("Full response when not logged in:", content)  # Depuración

        # Validar que existe un error
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        print("Error message received: -- SKILL NOT LOGGED", error_message)  # Imprime el mensaje exacto

        # Validar el mensaje específico
        assert 'Not logged in' in error_message  # Validación parcial para adaptarse a prefijos

    def test_create_skill_invalid_percent(self):
        response = self.query(
            CREATE_OR_UPDATE_SKILL,
            variables={
                "idSkill": 0,  # Para crear una nueva habilidad
                "skill": "Programming",
                "percent": 110
            },
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response for creating skill with invalid percent", content)

        # Validar que existe un error
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        print("Error message received: -- SKILL NOT LOGGED", error_message)  # Imprime el mensaje exacto

        # Validar el mensaje específico
        assert 'Invalid range for percent' in error_message  # Validación parcial para adaptarse a prefijos

    def test_create_skill_with_valid_id(self):
        # Realizar la mutación para crear una habilidad con un ID específico
        response = self.query(
            CREATE_OR_UPDATE_SKILL,
            variables={
                "idSkill": 0,  # Para crear una nueva habilidad
                "skill": "Programming",
                "percent": 90
            },
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response for creating skill with valid ID:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que la habilidad fue creada correctamente
        skill = content['data']['createSkill']
        assert skill['skill'] == "Programming"
        assert skill['percent'] == 90
        assert skill['postedBy']['username'] == self.user.username

    def test_create_skill_update(self):
        # Crear una habilidad existente en la base de datos
        self.skill1 = mixer.blend(
            Skill,
            skill="Old Skill",
            percent=50,
            posted_by=self.user
        )

        # Realizar la mutación para actualizar la habilidad existente
        response = self.query(
            CREATE_OR_UPDATE_SKILL,
            variables={
                "idSkill": self.skill1.id,
                "skill": "Updated Skill",
                "percent": 75
            },
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response when updating skill:", content)  # Depuración

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que el registro devuelto es correcto
        data = content['data']['createSkill']
        assert data['idSkill'] == self.skill1.id
        assert data['skill'] == "Updated Skill"
        assert data['percent'] == 75
        assert data['postedBy']['username'] == self.user.username

        # Obtener el registro actualizado en la base de datos
        skill = Skill.objects.get(id=self.skill1.id)

        # Validar que los datos en la base de datos son correctos
        assert skill.skill == "Updated Skill"
        assert skill.percent == 75
        assert skill.posted_by == self.user

    def test_delete_skill_existing(self):
        # Crear una habilidad existente
        self.skill1 = mixer.blend(
            Skill,
            skill="Test Skill",
            percent=50,
            posted_by=self.user
        )

        # Realizar la mutación para eliminar la habilidad
        response = self.query(
            DELETE_SKILL_MUTATION,
            variables={"idSkill": self.skill1.id},
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response when deleting existing skill:", content)

        # Validar que no hay errores
        self.assertResponseNoErrors(response)

        # Validar que la habilidad fue eliminada de la base de datos
        with self.assertRaises(Skill.DoesNotExist):
            Skill.objects.get(id=self.skill1.id)


    def test_delete_skill_nonexistent_id(self):
        # Realizar la mutación con un ID que no existe
        response = self.query(
            DELETE_SKILL_MUTATION,
            variables={"idSkill": 9999},  # ID inexistente
            headers=self.headers  # Usuario autenticado
        )
        content = json.loads(response.content)
        print("Response when deleting non-existent skill:", content)

        # Validar que se lanza la excepción 'Invalid Skill id!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Invalid Skill id!"


    def test_delete_skill_not_logged_in(self):
        # Crear una habilidad existente
        self.skill1 = mixer.blend(
            Skill,
            skill="Test Skill",
            percent=50,
            posted_by=self.user
        )

        # Realizar la mutación sin encabezado de autenticación
        response = self.query(
            DELETE_SKILL_MUTATION,
            variables={"idSkill": self.skill1.id}  # Sin autenticación
        )
        content = json.loads(response.content)
        print("Response when deleting without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"
