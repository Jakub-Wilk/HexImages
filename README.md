# HexImages - HexOcean recruitment task

## On env files

In a real project I would of course not include env files, and instead I would list all the important variables and what they represent, but as this is just a recruitment task I've decided to include the env files I used in the repository to make the project setup easier.

## Project setup - Dev mode

In the main project directory:

- run `docker compose build`
- run `docker compose run web python manage.py makemigrations`
- run `docker compose up`

That's all!

## Project setup - Production mode

After making sure there's no other service using port 80 (if you want to use other ports, you can do so in `dockerfile.prod.yml` in `ports` in the `nginx` service, but urls generated by the API will be lacking the port number), in the main project directory:

- run `docker compose -f dockerfile.prod.yml build`
- run `docker compose run web python manage.py makemigrations`
- run `docker compose run web python manage.py migrate`
- run `docker compose run web python manage.py createsuperuser` and follow the superuser setup
- run `docker compose run web python manage.py loaddata initial_data.json`
- run `docker compose up -d`

## On tests

I've written *some* tests to show that I can write them, but they are extremely lacking because I didn't have much time this week to work on this project. In a work environment I would of course write a complete test suite.