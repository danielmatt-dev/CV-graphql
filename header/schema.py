import graphene
from graphene_django import DjangoObjectType
from .models import Header
from users.schema import UserType
from django.db.models import Q

class HeaderType(DjangoObjectType):
    class Meta:
        model = Header

class Query(graphene.ObjectType):
    get_header = graphene.Field(HeaderType)
    
    def resolve_get_header(self, info):
        header = Header.objects.first()
        if not header:
            raise Exception("No Header exists.")
        return header

class CreateHeader(graphene.Mutation):
    name = graphene.String()
    actual_position = graphene.String()
    description = graphene.String()
    profile_picture = graphene.String()
    email = graphene.String()
    cellphone = graphene.String()
    location = graphene.String()
    github = graphene.String()
    posted_by = graphene.Field(UserType)

    class Arguments:
        name = graphene.String(required=True)
        actual_position = graphene.String(required=True)
        description = graphene.String(required=True)
        profile_picture = graphene.String(required=True)
        email = graphene.String(required=True)
        cellphone = graphene.String(required=True)
        location = graphene.String(required=True)
        github = graphene.String(required=True)

    def mutate(self, info, name, actual_position, description, profile_picture, email, cellphone, location, github):
        user = info.context.user or None
        print(user)

        if Header.objects.exists():
            raise Exception('A Header already exists. Delete the existing one before creating a new one.')

        header = Header(
            name=name,
            actual_position=actual_position,
            description=description,
            profile_picture=profile_picture,
            email=email,
            cellphone=cellphone,
            location=location,
            github=github,
            posted_by=user
        )
        header.save()

        return CreateHeader(
            name=header.name,
            actual_position=header.actual_position,
            description=header.description,
            profile_picture=header.profile_picture,
            email=header.email,
            cellphone=header.cellphone,
            location=header.location,
            github=header.github,
            posted_by=header.posted_by
        )

class UpdateHeader(graphene.Mutation):
    name = graphene.String()
    actual_position = graphene.String()
    description = graphene.String()
    profile_picture = graphene.String()
    email = graphene.String()
    cellphone = graphene.String()
    location = graphene.String()
    github = graphene.String()

    class Arguments:
        name = graphene.String()
        actual_position = graphene.String()
        description = graphene.String()
        profile_picture = graphene.String()
        email = graphene.String()
        cellphone = graphene.String()
        location = graphene.String()
        github = graphene.String()

    def mutate(self, info, name=None, actual_position=None, description=None, profile_picture=None, email=None, cellphone=None, location=None, github=None):
        user = info.context.user or None
        if user.is_anonymous:
            raise Exception("Not logged in!")

        # Verificar que existe un Header para actualizar
        header = Header.objects.first()
        if not header:
            raise Exception("No Header exists to update.")

        # Actualizar los campos proporcionados
        if name:
            header.name = name
        if actual_position:
            header.actual_position = actual_position
        if description:
            header.description = description
        if profile_picture:
            header.profile_picture = profile_picture
        if email:
            header.email = email
        if cellphone:
            header.cellphone = cellphone
        if location:
            header.location = location
        if github:
            header.github = github

        header.save()

        return UpdateHeader(
            name=header.name,
            actual_position=header.actual_position,
            description=header.description,
            profile_picture=header.profile_picture,
            email=header.email,
            cellphone=header.cellphone,
            location=header.location,
            github=header.github
        )


class DeleteHeader(graphene.Mutation):
    message = graphene.String()

    def mutate(self, info):
        user = info.context.user or None
        if user.is_anonymous:
            raise Exception('Not logged in!')
        print (user)

        if not Header.objects.exists():
            raise Exception('No Header exists to delete.')

        header = Header.objects.first()
        header.delete()

        return DeleteHeader(message="Header deleted successfully.")
    
class Mutation(graphene.ObjectType):
    create_header = CreateHeader.Field()
    delete_header = DeleteHeader.Field()
    update_header = UpdateHeader.Field()