#!/bin/sh
# Run the test suite against a database started in a throwaway container.
#   scripts/test-db.sh sqlite|postgresql|mysql|mariadb|oracle [pytest args]
# Needs Docker (except for sqlite) and the test dependencies: pip install -e '.[test]'
set -eu

DB="${1:?usage: $0 sqlite|postgresql|mysql|mariadb|oracle [pytest args]}"
shift
CONTAINER="launcher-test-$DB"
PYTEST="${PYTEST:-pytest}"

cleanup() { docker rm -f "$CONTAINER" >/dev/null 2>&1 || true; }

wait_for() {
	echo "Waiting for $DB..."
	i=0
	until docker exec "$CONTAINER" sh -c "$1" >/dev/null 2>&1; do
		i=$((i + 1))
		[ "$i" -lt 120 ] || { docker logs "$CONTAINER"; echo "$DB did not start"; exit 1; }
		sleep 2
	done
}

case "$DB" in
	sqlite)
		exec "$PYTEST" "$@"
		;;
	postgresql)
		trap cleanup EXIT
		docker run -d --rm --name "$CONTAINER" -p 15432:5432 -e POSTGRES_PASSWORD=pwd -e POSTGRES_DB=launcherdb postgres:16-alpine >/dev/null
		wait_for "pg_isready -U postgres -d launcherdb -h 127.0.0.1"
		export TEST_DB_URL="postgresql+psycopg://postgres:pwd@127.0.0.1:15432/launcherdb"
		;;
	mysql)
		trap cleanup EXIT
		docker run -d --rm --name "$CONTAINER" -p 13306:3306 -e MYSQL_ROOT_PASSWORD=pwd -e MYSQL_DATABASE=launcherdb mysql:8.4 >/dev/null
		wait_for "mysql -h 127.0.0.1 -uroot -ppwd -e 'select 1' launcherdb"
		export TEST_DB_URL="mysql+pymysql://root:pwd@127.0.0.1:13306/launcherdb"
		;;
	mariadb)
		trap cleanup EXIT
		docker run -d --rm --name "$CONTAINER" -p 13307:3306 -e MARIADB_ROOT_PASSWORD=pwd -e MARIADB_DATABASE=launcherdb mariadb:11 >/dev/null
		wait_for "healthcheck.sh --connect --innodb_initialized"
		export TEST_DB_URL="mysql+pymysql://root:pwd@127.0.0.1:13307/launcherdb"
		;;
	oracle)
		trap cleanup EXIT
		docker run -d --rm --name "$CONTAINER" -p 11521:1521 -e ORACLE_PASSWORD=pwd -e APP_USER=launcher -e APP_USER_PASSWORD=launcherpwd gvenzl/oracle-free:slim-faststart >/dev/null
		wait_for "healthcheck.sh"
		export TEST_DB_URL="oracle+oracledb://launcher:launcherpwd@127.0.0.1:11521/?service_name=FREEPDB1"
		;;
	*)
		echo "Unknown database: $DB" >&2
		exit 2
		;;
esac

"$PYTEST" "$@"
