from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import json
from django.contrib.auth import get_user_model
from header.models import Header
from hacker_news.schema import schema

# Mutaciones de GraphQL
CREATE_HEADER_MUTATION = '''
mutation CreateHeader($name: String!, $actualPosition: String!, $description: String!, $profilePicture: String!, $email: String!, $cellphone: String!, $location: String!, $github: String!) {
    createHeader(name: $name, actualPosition: $actualPosition, description: $description, profilePicture: $profilePicture, email: $email, cellphone: $cellphone, location: $location, github: $github) {
        name
        actualPosition
        description
        profilePicture
        email
        cellphone
        location
        github
        postedBy {
            username
        }
    }
}
'''

DELETE_HEADER_MUTATION = '''
mutation DeleteHeader {
    deleteHeader {
        message
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


class HeaderTestCase(GraphQLTestCase):
    GRAPHQL_URL = "http://localhost:8000/graphql/"
    GRAPHQL_SCHEMA = schema

    def setUp(self):
        # Crear un usuario para las pruebas
        response_user = self.query(
            CREATE_USER_MUTATION,
            variables={'email': 'testuser@example.com', 'username': 'testuser', 'password': 'password123'}
        )
        content_user = json.loads(response_user.content)
        print("Create user response:", content_user)

        # Obtener un token para el usuario
        response_token = self.query(
            LOGIN_USER_MUTATION,
            variables={'username': 'testuser', 'password': 'password123'}
        )
        content_token = json.loads(response_token.content)
        token = content_token['data']['tokenAuth']['token']
        self.headers = {"AUTHORIZATION": f"JWT {token}"}

        # Crear un encabezado de ejemplo
        self.user = get_user_model().objects.get(username="testuser")
        self.header = mixer.blend(
            Header,
            name="Test User",
            actual_position="Software Developer",
            description="Building scalable applications.",
            profile_picture="https://example.com/image.jpg",
            email="testuser@example.com",
            cellphone="1234567890",
            location="Test City",
            github="https://github.com/testuser",
            posted_by=self.user
        )

    def test_create_header_success(self):
        # Probar la creación de un nuevo encabezado
        Header.objects.all().delete()  # Asegurarse de que no exista un encabezado

        response = self.query(
            CREATE_HEADER_MUTATION,
            variables={
                "name": "New User",
                "actualPosition": "Frontend Developer",
                "description": "Creating amazing user experiences.",
                "profilePicture": "https://example.com/newimage.jpg",
                "email": "newuser@example.com",
                "cellphone": "9876543210",
                "location": "New City",
                "github": "https://github.com/newuser"
            },
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Create header response:", content)

        self.assertResponseNoErrors(response)
        data = content['data']['createHeader']
        assert data['name'] == "New User"
        assert data['email'] == "newuser@example.com"

        # Verificar la base de datos
        header = Header.objects.get(name="New User")
        assert header.actual_position == "Frontend Developer"

    def test_create_header_already_exists(self):
        # Probar la creación de un encabezado cuando ya existe uno
        response = self.query(
            CREATE_HEADER_MUTATION,
            variables={
                "name": "Duplicate User",
                "actualPosition": "Backend Developer",
                "description": "Handling server-side logic.",
                "profilePicture": "https://example.com/duplicateimage.jpg",
                "email": "duplicateuser@example.com",
                "cellphone": "1231231234",
                "location": "Duplicate City",
                "github": "https://github.com/duplicateuser"
            },
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Create header response (duplicate):", content)

        assert 'errors' in content
        assert content['errors'][0]['message'] == "A Header already exists. Delete the existing one before creating a new one."

    def test_delete_header_success(self):
        # Probar la eliminación de un encabezado existente
        response = self.query(
            DELETE_HEADER_MUTATION,
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Delete header response:", content)

        self.assertResponseNoErrors(response)
        assert content['data']['deleteHeader']['message'] == "Header deleted successfully."

        # Verificar que el encabezado fue eliminado
        assert not Header.objects.exists()

    def test_delete_header_not_logged_in(self):
        # Probar la eliminación sin autenticación
        response = self.query(DELETE_HEADER_MUTATION)
        content = json.loads(response.content)
        print("Delete header without login:", content)

        assert 'errors' in content
        assert content['errors'][0]['message'] == "Not logged in!"

    def test_delete_header_no_existing(self):
        # Probar la eliminación cuando no existe un encabezado
        Header.objects.all().delete()  # Asegurarse de que no exista un encabezado

        response = self.query(
            DELETE_HEADER_MUTATION,
            headers=self.headers
        )
        content = json.loads(response.content)
        print("Delete header response (no existing):", content)

        assert 'errors' in content
        assert content['errors'][0]['message'] == "No Header exists to delete."

    def test_create_multiple_headers_fails(self):
        """
        Verifica que intentar crear múltiples instancias de Header
        lance una excepción personalizada.
        """
        with self.assertRaises(Exception) as context:
            Header.objects.create(
                name="Second Header",
                actual_position="Designer",
                description="Second instance",
                profile_picture="https://example.com/second.jpg",
                email="seconduser@example.com",
                cellphone="2222222222",
                location="Second City",
                github="https://github.com/seconduser",
                posted_by=self.user
            )
        assert str(context.exception) == "Only one header instance is allowed"

    def test_update_existing_header_success(self):
        """
        Verifica que se pueda actualizar una instancia existente sin lanzar excepciones.
        """
        self.header.name = "Updated Header"
        self.header.save()  # No debe lanzar excepciones
        updated_header = Header.objects.get(pk=self.header.pk)
        assert updated_header.name == "Updated Header"

    def test_header_str_method(self):
        """
        Verifica que el método __str__ del modelo Header retorne el valor del campo name.
        """
        expected_str = self.header.name
        assert str(self.header) == expected_str

    def test_update_header(self):
        # Actualizar el Header existente
        response = self.query(
            '''
            mutation UpdateHeader(
            $name: String,
            $actualPosition: String,
            $description: String,
            $profilePicture: String,
            $email: String,
            $cellphone: String,
            $location: String,
            $github: String
            ) {
            updateHeader(
                name: $name,
                actualPosition: $actualPosition,
                description: $description,
                profilePicture: $profilePicture,
                email: $email,
                cellphone: $cellphone,
                location: $location,
                github: $github
            ) {
                name
                actualPosition
                description
                profilePicture
                email
                cellphone
                location
                github
            }
            }
            ''',
            variables={
                "name": "Updated Name",
                "actualPosition": "Updated Position",
                "description": "Updated Description",
                "profilePicture": "https://example.com/new_image.jpg",
                "email": "updatedemail@example.com",
                "cellphone": "1234567890",
                "location": "Updated Location",
                "github": "https://github.com/updateduser"
            },
            headers=self.headers
        )
        content = json.loads(response.content)

        # Verificar que no hay errores
        self.assertResponseNoErrors(response)

        # Verificar que los datos se actualizaron correctamente
        self.header.refresh_from_db()
        assert self.header.name == "Updated Name"
        assert self.header.actual_position == "Updated Position"
        assert self.header.email == "updatedemail@example.com"


    def test_update_header_not_logged_in(self):
        Header.objects.all().delete()

        # Crear un Header inicial
        header = Header.objects.create(
            name="Initial Name",
            actual_position="Initial Position",
            description="Initial Description",
            profile_picture="https://example.com/image.jpg",
            email="initial@example.com",
            cellphone="9876543210",
            location="Initial Location",
            github="https://github.com/initialuser",
            posted_by=self.user
        )

        # Actualizar el Header existente
        response = self.query(
            '''
            mutation UpdateHeader(
            $name: String,
            $actualPosition: String,
            $description: String,
            $profilePicture: String,
            $email: String,
            $cellphone: String,
            $location: String,
            $github: String
            ) {
            updateHeader(
                name: $name,
                actualPosition: $actualPosition,
                description: $description,
                profilePicture: $profilePicture,
                email: $email,
                cellphone: $cellphone,
                location: $location,
                github: $github
            ) {
                name
                actualPosition
                description
                profilePicture
                email
                cellphone
                location
                github
            }
            }
            ''',
            variables={
                "name": "Updated Name",
                "actualPosition": "Updated Position",
                "description": "Updated Description",
                "profilePicture": "https://example.com/new_image.jpg",
                "email": "updatedemail@example.com",
                "cellphone": "1234567890",
                "location": "Updated Location",
                "github": "https://github.com/updateduser"
            },
        )
        content = json.loads(response.content)
        print("Response when deleting without authentication:", content)

        # Validar que se lanza la excepción 'Not logged in!'
        assert 'errors' in content
        error_message = content['errors'][0]['message']
        assert error_message == "Not logged in!"

    def test_get_header_success(self):
        # Consulta para obtener el Header existente
        response = self.query(
            '''
            query {
                getHeader {
                    name
                    actualPosition
                    description
                    profilePicture
                    email
                    cellphone
                    location
                    github
                    postedBy {
                        username
                    }
                }
            }
            ''',
            headers=self.headers 
        )
        content = json.loads(response.content)

        # Verificar que no hay errores
        self.assertResponseNoErrors(response)

        # Verificar los datos devueltos
        data = content["data"]["getHeader"]
        assert data["name"] == "Test User"
        assert data["actualPosition"] == "Software Developer"
        assert data["description"] == "Building scalable applications."
        assert data["profilePicture"] == "https://example.com/image.jpg"
        assert data["email"] == "testuser@example.com"
        assert data["cellphone"] == "1234567890"
        assert data["location"] == "Test City"
        assert data["github"] == "https://github.com/testuser"
        assert data["postedBy"]["username"] == "testuser"

    def test_get_header_not_exists(self):
        # Eliminar el Header existente
        Header.objects.all().delete()

        # Intentar obtener el Header
        response = self.query(
            '''
            query {
                getHeader {
                    name
                    actualPosition
                }
            }
            ''',
            headers=self.headers
        )
        content = json.loads(response.content)

        # Verificar que hay un error
        assert "errors" in content
        assert content["errors"][0]["message"] == "No Header exists."

    def test_update_header_no_header_exists(self):
        # Eliminar todos los Headers existentes
        Header.objects.all().delete()

        # Intentar actualizar un Header inexistente
        response = self.query(
            '''
            mutation UpdateHeader(
            $name: String,
            $actualPosition: String,
            $description: String,
            $profilePicture: String,
            $email: String,
            $cellphone: String,
            $location: String,
            $github: String
            ) {
            updateHeader(
                name: $name,
                actualPosition: $actualPosition,
                description: $description,
                profilePicture: $profilePicture,
                email: $email,
                cellphone: $cellphone,
                location: $location,
                github: $github
            ) {
                name
                actualPosition
                description
                profilePicture
                email
                cellphone
                location
                github
            }
            }
            ''',
            variables={
                "name": "Updated Name",
                "actualPosition": "Updated Position",
                "description": "Updated Description",
                "profilePicture": "https://example.com/new_image.jpg",
                "email": "updatedemail@example.com",
                "cellphone": "1234567890",
                "location": "Updated Location",
                "github": "https://github.com/updateduser"
            },
            headers=self.headers
        )
        content = json.loads(response.content)

        # Verificar que hay un error
        print("Response when no Header exists to update:", content)  # Depuración
        assert "errors" in content
        assert content["errors"][0]["message"] == "No Header exists to update."
