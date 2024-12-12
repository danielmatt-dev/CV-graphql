import graphene
import graphql_jwt

import links.schema
import users.schema
import education.schema
import archivements.schema
import interest.schema
import language.schema
import skills.schema
import workexperience.schema
import header.schema

class Query(header.schema.Query ,workexperience.schema.Query, skills.schema.Query ,language.schema.Query ,interest.schema.Query, archivements.schema.Query, education.schema.Query, users.schema.Query, links.schema.Query, graphene.ObjectType):
    pass

class Mutation(header.schema.Mutation, workexperience.schema.Mutation, skills.schema.Mutation ,language.schema.Mutation ,interest.schema.Mutation ,archivements.schema.Mutation, education.schema.Mutation, users.schema.Mutation, links.schema.Mutation, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)