.PHONY: run test lint format migrate collectstatic docker-up

run:
	python manage.py runserver

test:
	python manage.py test

lint:
	ruff check .

format:
	ruff format .

migrate:
	python manage.py migrate

collectstatic:
	python manage.py collectstatic --noinput

docker-up:
	docker compose up --build