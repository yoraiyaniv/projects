run_server:
	cd postgresql; docker compose up flask_server -d

close_server:
	cd postgresql; docker compose stop flask_server

rebuild_tables:
	python3 core/rebuild_tables.py

build_db:
	cd postgresql; docker compose up postgres -d

stop_db:
	cd postgresql; docker compose stop postgres

destroy_db:
	cd postgresql; docker compose down

