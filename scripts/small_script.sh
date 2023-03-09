psql -v ON_ERROR_STOP=1 --username postgres --dbname postgres --host localhost --port 5432 <<EOSQL
select * from test_data;
EOSQL
