import graphene
from graphene_django import DjangoObjectType
from .models import Interest
from users.schema import UserType
from django.db.models import Q

class InterestType(DjangoObjectType):
    class Meta:
        model = Interest

class Query(graphene.ObjectType):
    interest = graphene.List(InterestType, search=graphene.String(required=False))
    interestById = graphene.Field(InterestType, idInterest=graphene.Int())

    def resolve_interest(self, info, search=None, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not logged in!')

        print("Authenticated user:", user)
        print("Search value:", search)

        # Construir el filtro base
        filter = Q(posted_by=user)

        # Caso: Si search es None o "*", devuelve los primeros 10 registros
        if not search or search == "*":
            interests = Interest.objects.filter(filter)[:10]
            print("Interests returned (no filter or wildcard):", interests)
            return interests

        # Caso: Filtrar por interés específico
        filter &= Q(name__icontains=search)
        interests = Interest.objects.filter(filter)
        print("Filtered interests returned:", interests)
        return interests

    def resolve_interestById(self, info, idInterest, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not logged in!')
        print(user)

        filter = (
            Q(posted_by=user) & Q(id = idInterest)
        ) 
        return Interest.objects.filter(filter).first()

class CreateInterest(graphene.Mutation):
    idInterest = graphene.Int()
    name = graphene.String()
    posted_by = graphene.Field(UserType)

    class Arguments:
        idInterest = graphene.Int()
        name = graphene.String()

    def mutate(self, info, idInterest, name):
        user = info.context.user
        if user.is_anonymous:  # Validar si el usuario no está autenticado
            raise Exception('Not logged in!')

        currentInterest = Interest.objects.filter(id=idInterest).first()
        print(currentInterest)

        interest = Interest(
            name=name,
            posted_by=user
        )

        if currentInterest:
            interest.id = currentInterest.id

        interest.save()

        return CreateInterest(
            idInterest=interest.id,
            name=interest.name,
            posted_by=interest.posted_by
        )
    
class DeleteInterest(graphene.Mutation):
    idInterest = graphene.Int()

    class Arguments:
        idInterest = graphene.Int()

    def mutate(self, info, idInterest):
        user = info.context.user or None 

        if user.is_anonymous:
            raise Exception('Not logged in!')
        print(user)

        currentInterest = Interest.objects.filter(id=idInterest).first()
        print(currentInterest)

        if not currentInterest:
            raise Exception('Invalid Interest id!')
        
        currentInterest.delete()

        return CreateInterest(
            idInterest = idInterest
        )
    
class Mutation(graphene.ObjectType):
    create_interest = CreateInterest.Field()
    delete_interest = DeleteInterest.Field()