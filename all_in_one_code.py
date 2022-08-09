# Command to start this app inside docker --> (ordervenv) C:\Users\asahu23\orderservice\code>docker-compose run app uvicorn testing:app --host 0.0.0.0 --port 8300 --reload

# ++++++++++++++++++++++++++++ db_config +++++++++++++++++++++++++++++++++++++++

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("postgresql+psycopg2://postgres:password@db:5432/post_db")
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()  # This is for query property of graphene


# ++++++++++++++++++++++++++++ models +++++++++++++++++++++++++++++++++++++++

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func


class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    author = Column(String)
    content = Column(String)
    time_created = Column(DateTime(timezone=True), server_default=func.now())


# ++++++++++++++++++++++++++++ schemas +++++++++++++++++++++++++++++++++++++++

from graphene_sqlalchemy import SQLAlchemyObjectType
from pydantic import BaseModel


class PostSchema(BaseModel):
    title: str
    content: str


class PostModel(SQLAlchemyObjectType):
    class Meta:
        model = Post


# ++++++++++++++++++++++++++++ Authentication with JWT +++++++++++++++++++++++++++++++++++++++

from datetime import datetime, timedelta

import jwt

# to get a string like this run --> openssl rand -hex 32
secret_key = "89023f0j2039jf90jkakmciumcses9mcs99mcs93c48ym72tmarf737mc7h47wna4c8791289h8f1h3f8h376fh8bf4"
algorithm = "HS256"


def create_access_token(data, expires_delta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode = "demouser1"
    to_encode.update({"exp": expire})
    access_token = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return access_token


def decode_access_token(data):
    token_data = jwt.decode(data, secret_key, algorithms=algorithm)
    return token_data


# ++++++++++++++++++++++++++++ Generate Token +++++++++++++++++++++++++++++++++++++++


class GenerateToken(graphene.Mutation):
    class Arguments:
        username = "demouser1"

    ok = graphene.Boolean()
    token = graphene.String()

    @staticmethod
    def mutate(root, info, username):
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(data={"user": username}, expires_delta=access_token_expires)
        return GenerateToken(token=access_token)


# ++++++++++++++++++++++++++++ main/GraphQL +++++++++++++++++++++++++++++++++++++++

from datetime import timedelta

import graphene
from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from graphql import GraphQLError
from jwt import PyJWTError
from starlette.graphql import GraphQLApp

db = db_session.session_factory()
app = FastAPI()


class Query(graphene.ObjectType):

    all_posts = graphene.List(PostModel)
    post_by_id = graphene.Field(PostModel, post_id=graphene.Int(required=True))

    def resolve_all_posts(self, info):
        query = PostModel.get_query(info)
        return query.all()

    def resolve_post_by_id(self, info, post_id):
        return db.query(Post).filter(Post.id == post_id).first()


class CreateNewPost(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)

    result = graphene.String()

    @staticmethod
    def mutate(root, info, title, content):
        post = PostSchema(title=title, content=content)
        db_post = Post(title=post.title, content=post.content)
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        result = "Added new post"
        return CreateNewPost(result=result)


class CreateNewPostWithJWT(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        token = graphene.String(required=True)

    result = graphene.String()

    @staticmethod
    def mutate(root, info, title, content, token):

        try:
            payload = decode_access_token(data=token)
            username = payload.get("user")

            if username == "demouser1":
                post = PostSchema(title=title, content=content)
                db_post = Post(title=post.title, content=post.content)
                db.add(db_post)
                db.commit()
                db.refresh(db_post)
                result = "Added new post with JWT"
        except PyJWTError:
            raise GraphQLError("Invalid credentials 2")

        return CreateNewPostWithJWT(result=result)


class PostMutations(graphene.ObjectType):
    create_new_post = CreateNewPost.Field()
    create_new_post_with_jwt = CreateNewPostWithJWT.Field()


app.add_route("/graphql", GraphQLApp(schema=graphene.Schema(query=Query, mutation=PostMutations)))


# ++++++++++++++++++++++++++++ Celery worker +++++++++++++++++++++++++++++++++++++++

## celery worker will perform action on celery_worker.py file because same is configured in docker compose file, byt just for refernece I have pasted the code here.
## This command from docker file points to the celery_worker.py file --> command: celery -A celery_worker.celery worker --loglevel=info

# import time
# from celery import Celery

# celery = Celery(__name__)
# celery.conf.broker_url = "redis://redis:6379/0"
# celery.conf.result_backend = "redis://redis:6379/0"

# @celery.task(name="create_task")
# def create_task(a, b, c):
#     time.sleep(a)
#     return b + c


# ++++++++++++++++++++++++++++ Celery flower +++++++++++++++++++++++++++++++++++++++

# its configured in docker compose file.


# ++++++++++++++++++++++++++++ run the celery task  +++++++++++++++++++++++++++++++++++++++

## please add this code above the route code.

from celery_worker import create_task


@app.post("/ex1")
def run_task(data=Body(...)):
    amount = int(data["amount"])
    x = data["x"]
    y = data["y"]
    task = create_task.delay(amount, x, y)
    return JSONResponse({"Result": task.get()})
