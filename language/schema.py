import graphene
from graphene_django import DjangoObjectType
from .models import Language
from users.schema import UserType
from django.db.models import Q

class LanguageType(DjangoObjectType):
    class Meta:
        model = Language

class Query(graphene.ObjectType):
    languages = graphene.List(LanguageType, search=graphene.String(required=False))
    languageById = graphene.Field(LanguageType, idLanguage=graphene.Int())

    def resolve_languages(self, info, search=None, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not logged in!')

        print("Authenticated user:", user)
        print("Search value:", search)

        # Construir el filtro base
        filter = Q(posted_by=user)

        # Caso: Si search es None o "*", devuelve los primeros 10 registros
        if not search or search == "*":
            languages = Language.objects.filter(filter)[:10]
            print("languages returned (no filter or wildcard):", languages)
            return languages

        # Caso: Filtrar por interés específico
        filter &= Q(language__icontains=search)
        languages = Language.objects.filter(filter)
        print("Filtered languages returned:", languages)
        return languages
        
    def resolve_languageById(self, info, idLanguage, **kwargs):
        user = info.context.user  
        if user.is_anonymous:
            raise Exception('Not logged in!')
        print(user)

        filter = (
            Q(posted_by=user) & Q(id=idLanguage)
        )
        return Language.objects.filter(filter).first()
    
class CreateLanguage(graphene.Mutation):
    idLanguage = graphene.Int()
    language = graphene.String()
    posted_by = graphene.Field(UserType)

    class Arguments:
        idLanguage = graphene.Int()
        language = graphene.String()

    def mutate(self, info, idLanguage, language):
        user = info.context.user
        if user.is_anonymous:  # Validar si el usuario no está autenticado
            raise Exception('Not logged in!')

        currentLanguage = Language.objects.filter(id=idLanguage).first()
        print(currentLanguage)

        language = Language(
            language = language,
            posted_by = user
        )

        if currentLanguage:
            language.id = currentLanguage.id

        language.save()    

        return CreateLanguage(
            idLanguage = language.id,
            language = language.language,
            posted_by = language.posted_by
        )
    
class DeleteLanguage(graphene.Mutation):
    idLanguage = graphene.Int()

    class Arguments:
        idLanguage= graphene.Int()

    def mutate(self, info, idLanguage):
        user = info.context.user or None

        if user.is_anonymous:
            raise Exception('Not logged in!')
        print(user)

        currentLanguage = Language.objects.filter(id=idLanguage).first()
        print (currentLanguage)

        if not currentLanguage:
            raise Exception('Invalid Language id!')
        
        currentLanguage.delete()

        return CreateLanguage(
            idLanguage = idLanguage
        )
    
class Mutation(graphene.ObjectType):
    create_language = CreateLanguage.Field()
    delete_language = DeleteLanguage.Field()