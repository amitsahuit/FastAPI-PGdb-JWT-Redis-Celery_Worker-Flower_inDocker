

fastapi uvicorn sqlalchemy graphene graphene-sqlalchemy alembic psycopg2 black python-dotenv

alembic init alembic

docker-compose run app alembic revision --autogenerate -m "New Migration" 
docker-compose run app alembic upgrade head

mutation CreateNewPost{
  createNewPost(title:"new title1", content:"new content") {
    ok
  }
}

query{
  allPosts{
    title
  }
}

query{
  postById(postId:2){
    id
  	title
    content
  }
}

mutation newuser{
  createNewUser(username:"test1", password:"test1") {
    ok
  }
}

mutation authenticateUser{
  authenticateUser(username:"test10", password:"test10") {
    ok
    token
  }
}


eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiYW1pdCIsImV4cCI6MTY2MDAwOTM3NX0.c3itStxkzpcp1CgPxymG8x19emTm0MKNs4m69fOqZx0

mutation CreateNewPost{
  createNewPost(title:"new title1", content:"new content", token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoidGVzdDIwIiwiZXhwIjoxNjI1Njc4MzA1fQ.bUxdKz1KWougGZw-vRLdBGZN87WloCg-6Rai-bCObAc") {
    result
  }
}