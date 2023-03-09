      psql -v ON_ERROR_STOP=1 --username postgres --dbname postgres --host localhost --port 5432 --port 5432 <<EOSQL
        -- drop
        drop table if exists test_data;
        drop table if exists test_data_history;
        
        -- create
        create table test_data (id serial PRIMARY KEY, amount numeric(12,8), curveStart TIMESTAMP);
        create table test_data_history (id serial, amount numeric(12,8), curveStart TIMESTAMP, curveEnd TIMESTAMP);
        CREATE INDEX ON test_data_history (id); -- this has to be updated?

        -- insert
        insert into test_data (amount, curveStart) values (1.0, TO_TIMESTAMP('6/1/2022', 'MM/DD/YYYY'));

        -- confirm 1
        select id,amount from test_data;

        -- update (via scd2)
        \set _currenttime NOW() -- this is when the update is happening
        with data as (
            select id, amount, curveStart from test_data where id = '1'
        ),
        backup as (
            insert into test_data_history (id, amount, curveStart) 
            select id, amount, curveStart
            from data
        )
        update test_data set amount = 2.0 where id = 1;
        select * from test_data;
        select * from test_data_history;
EOSQL
