import graphene
from graphene_django import DjangoObjectType
from .models import Skill
from users.schema import UserType
from django.db.models import Q

class SkillType(DjangoObjectType):
    class Meta:
        model = Skill

class Query(graphene.ObjectType):
    skill = graphene.List(SkillType, search=graphene.String(required=False))
    skillById = graphene.Field(SkillType, idSkill=graphene.Int())

    def resolve_skill(self, info, search=None, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not logged in!')

        print("Authenticated user:", user)
        print("Search value:", search)

        # Construir el filtro base
        filter = Q(posted_by=user)

        # Caso: Si search es None o "*", devuelve los primeros 10 registros
        if not search or search == "*":
            skills = Skill.objects.filter(filter)[:10]
            print("skills returned (no filter or wildcard):", skills)
            return skills

        # Caso: Filtrar por interés específico
        filter &= Q(skill__icontains=search)
        skills = Skill.objects.filter(filter)
        print("Filtered skills returned:", skills)
        return skills

        
    def resolve_skillById(self, info, idSkill, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not logged in!')
        print(user)

        filter = (
            Q(posted_by=user) & Q(id=idSkill)
        )
        return Skill.objects.filter(filter).first()

class CreateSkill(graphene.Mutation):
    idSkill = graphene.Int()
    skill = graphene.String()
    percent = graphene.Int()
    posted_by = graphene.Field(UserType)

    class Arguments:
        idSkill = graphene.Int()
        skill = graphene.String()
        percent = graphene.Int()

    def mutate(self, info, idSkill, skill, percent):
        if percent < 0 or percent > 100:
            raise Exception('Invalid range for percent')
        
        user = info.context.user
        if user.is_anonymous:  # Validar si el usuario no está autenticado
            raise Exception('Not logged in!')

        currentSkill = Skill.objects.filter(id=idSkill).first()
        print(currentSkill)

        skill = Skill(
            skill=skill,
            percent=percent,
            posted_by=user
        )

        if currentSkill:
            skill.id = currentSkill.id  
        
        skill.save()

        return CreateSkill(
            idSkill=skill.id,
            skill=skill.skill,
            percent=skill.percent,
            posted_by=skill.posted_by
        )
    
class DeleteSkill(graphene.Mutation):
    idSkill = graphene.Int()

    class Arguments:
        idSkill = graphene.Int()

    def mutate(self, info, idSkill):
        user = info.context.user or None
        if user.is_anonymous:
            raise Exception('Not logged in!')
        print (user) 

        currentSkill = Skill.objects.filter(id=idSkill).first()
        print(currentSkill)

        if not currentSkill:
            raise Exception('Invalid Skill id!')
        
        currentSkill.delete()

        return CreateSkill(
            idSkill=idSkill
        )
    
class Mutation(graphene.ObjectType):
    create_skill = CreateSkill.Field()
    delete_skill = DeleteSkill.Field()