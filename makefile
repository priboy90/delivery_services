up:
	docker-compose up -d db

down:
	docker-compose down


logs:
	docker-compose logs -f db

connect:
	docker exec -it db psql -U postgres -d postgres

clean:
	docker-compose down -v
