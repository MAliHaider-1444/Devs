next

* scd-2 testing all control areas
* api upload for individual files
* api download for simple filters

todo

* historical updates working from code
* basic dashboard
* read only user for API (no updates from API at this point)
* confirm date is handled correctly (vm time/tz, db time/tz, api time/tz)
* move to aws
* backup process



--- old notes


Tracking poc for:

* influxdb
* grafana + influxdb
* postgres
* grafana + postgres
* tableau
* tableau + influxdb + 
* tableau + postgres

## influxdb
### set up influxdb

* on mac
  * install binaries (not homebrew)

```
influx_test % ./influxd --reporting-disabled
...
```

```
# note these is created
influx_test % ls ~/.influxdbv2/
configs		engine		influxd.bolt	influxd.sqlite
```

```
# setup user, organization, and initial bucket
influx_test % influx setup        
> Welcome to InfluxDB 2.0!
? Please type your primary username admin
? Please type your password **********
? Please type your password again **********
? Please type your primary organization name truelightenergy
? Please type your primary bucket name trueprice
? Please type your retention period in hours, or 0 for infinite 0
? Setup with these parameters?
  Username:          admin
  Organization:      truelightenergy
  Bucket:            trueprice
  Retention Period:  infinite
 Yes
User	Organization	Bucket
admin	truelightenergy	trueprice
```

```
influxdb2_darwin_amd64 % influx config
Active	Name	URL			Org
*	default	http://localhost:8086	truelightenergy

influxdb2_darwin_amd64 % influx user list
ID			Name
0a6cf51c3c0e4000	admin
```

```
influxdb2_darwin_amd64 % influx user create -n all -o truelightenergy
ID			Name
0a6cf5e1a1ce4000	all
WARN: initial password not set for user, use `influx user password` to set it
```

```
influxdb2_darwin_amd64 % influx user password --name all           
? Please type new password for "all" *********
? Please type new password for "all" again *********
Successfully updated password for user "all"
```

```
influxdb2_darwin_amd64 % influx auth create --all-access --org truelightenergy --user all
ID			Description	Token												User Name	User ID			Permissions
0a6cf705b9ce4000			t84XWlwvzVLoUE4AD7PZZoSuuc32oibDphD86TlPRcrHJiMkfQUi2-ZGvuEi1A3OXX_6aYDordP4VEdStCce8Q==	all		0a6cf5e1a1ce4000	[read:orgs/421f399a38639f91/authorizations write:orgs/421f399a38639f91/authorizations read:orgs/421f399a38639f91/buckets write:orgs/421f399a38639f91/buckets read:orgs/421f399a38639f91/dashboards write:orgs/421f399a38639f91/dashboards read:/orgs/421f399a38639f91 read:orgs/421f399a38639f91/sources write:orgs/421f399a38639f91/sources read:orgs/421f399a38639f91/tasks write:orgs/421f399a38639f91/tasks read:orgs/421f399a38639f91/telegrafs write:orgs/421f399a38639f91/telegrafs read:/users/0a6cf5e1a1ce4000 write:/users/0a6cf5e1a1ce4000 read:orgs/421f399a38639f91/variables write:orgs/421f399a38639f91/variables read:orgs/421f399a38639f91/scrapers write:orgs/421f399a38639f91/scrapers read:orgs/421f399a38639f91/secrets write:orgs/421f399a38639f91/secrets read:orgs/421f399a38639f91/labels write:orgs/421f399a38639f91/labels read:orgs/421f399a38639f91/views write:orgs/421f399a38639f91/views read:orgs/421f399a38639f91/documents write:orgs/421f399a38639f91/documents read:orgs/421f399a38639f91/notificationRules write:orgs/421f399a38639f91/notificationRules read:orgs/421f399a38639f91/notificationEndpoints write:orgs/421f399a38639f91/notificationEndpoints read:orgs/421f399a38639f91/checks write:orgs/421f399a38639f91/checks read:orgs/421f399a38639f91/dbrp write:orgs/421f399a38639f91/dbrp read:orgs/421f399a38639f91/notebooks write:orgs/421f399a38639f91/notebooks read:orgs/421f399a38639f91/annotations write:orgs/421f399a38639f91/annotations read:orgs/421f399a38639f91/remotes write:orgs/421f399a38639f91/remotes read:orgs/421f399a38639f91/replications write:orgs/421f399a38639f91/replications]
```

### write data

```
# using "all" user

```

### read data

```
# using "all" user
```

### update data

### API

### backup

### replicate

### shard

## granfana
### influxdb datasource
### API

## postgres
TimescaleDB is built on postgres
Postgres is hosted in all major clouds
Postgres has sql
### set up postgres

```
postgres_test % docker container run --name some-postgres -e POSTGRES_PASSWORD=postgres -p 0.0.0.0:5432:5432 -d postgres

# for grafana, use host.docker.internal:5432
```

```
postgres_test % docker container exec -it some-postgres psql -U postgres
psql (15.1 (Debian 15.1-1.pgdg110+1))
Type "help" for help.

postgres=#
```

```
postgres=# \db
       List of tablespaces
    Name    |  Owner   | Location 
------------+----------+----------
 pg_default | postgres | 
 pg_global  | postgres | 
(2 rows)
```

### write data

```
postgres=# create database trueprice;
CREATE DATABASE
postgres=# \l
                                                List of databases
   Name    |  Owner   | Encoding |  Collate   |   Ctype    | ICU Locale | Locale Provider |   Access privileges   
-----------+----------+----------+------------+------------+------------+-----------------+-----------------------
 postgres  | postgres | UTF8     | en_US.utf8 | en_US.utf8 |            | libc            | 
 template0 | postgres | UTF8     | en_US.utf8 | en_US.utf8 |            | libc            | =c/postgres          +
           |          |          |            |            |            |                 | postgres=CTc/postgres
 template1 | postgres | UTF8     | en_US.utf8 | en_US.utf8 |            | libc            | =c/postgres          +
           |          |          |            |            |            |                 | postgres=CTc/postgres
 trueprice | postgres | UTF8     | en_US.utf8 | en_US.utf8 |            | libc            | 
(4 rows)

postgres=# \c trueprice;
You are now connected to database "trueprice" as user "postgres".

trueprice=# create table data (id serial PRIMARY KEY, amount numeric(12,8), hour TIMESTAMP);
CREATE TABLE

trueprice=# insert into data (amount, hour) values (1.0, TO_TIMESTAMP('6/1/2022', 'MM/DD/YYYY'));
INSERT 0 1
```

### read data

```
trueprice=# select * from data;
 id |   amount   |        hour         
----+------------+---------------------
  1 | 1.00000000 | 2022-06-01 00:00:00
(1 row)
```

### API
### update data
### backup
### replicate
### shard

## granfana
### postgres datasource
### API

## tableau
### influxdb datasource
### postgres datasource
### API
### tableau management

## volatility notifications
### API
## in-active notifications
### API

## event sourcing






--- scratch

select exists(select 1 from trueprice.nyiso_forwardcurve where curvestart='2022-12-09 11:59:59'and strip='7X8')
UNION ALL
select exists(select 1 from trueprice.nyiso_forwardcurve where curvestart>='2022-12-09' and curvestart<'2022-12-09 11:59:59' and strip='7X8')
UNION ALL
select exists(select 1 from trueprice.nyiso_forwardcurve where curvestart>'2022-12-09 11:59:59' and curvestart<'2022-12-10' and strip='7X8')


select exists(select 1 from trueprice.nyiso_forwardcurve where curvestart='2023-01-09 08:47:00'and strip='5X16')
UNION ALL
select exists(select 1 from trueprice.nyiso_forwardcurve where curvestart>='2023-01-09' and curvestart<'2023-01-09 08:47:00' and strip='5X16')
UNION ALL
select exists(select 1 from trueprice.nyiso_forwardcurve where curvestart>'2023-01-09 08:47:00' and curvestart<'2023-01-10' and strip='5X16')


# NYISO (done)
            backup_query = f'''
with current as (
    -- get the current rows in the database, all of them, not just things that will change
    select id, strip, curvestart, zone_a_amount, zone_b_amount, zone_c_amount, zone_d_amount, zone_e_amount, zone_f_amount, zone_g_amount, zone_h_amount, zone_i_amount, zone_j_amount, zone_k_amount from trueprice.{m.controlArea}_forwardcurve where curvestart>='{sod}' and curvestart<='{eod}' and strip='{m.strip}'
),
backup as (
    -- take current rows and insert into database but with a new "curveend" timestamp
    insert into trueprice.{m.controlArea}_forwardcurve_history (id, strip, curvestart, curveend, zone_a_amount, zone_b_amount, zone_c_amount, zone_d_amount, zone_e_amount, zone_f_amount, zone_g_amount, zone_h_amount, zone_i_amount, zone_j_amount, zone_k_amount)
    select id, strip, curvestart, '{curveend}' as curveend, zone_a_amount, zone_b_amount, zone_c_amount, zone_d_amount, zone_e_amount, zone_f_amount, zone_g_amount, zone_h_amount, zone_i_amount, zone_j_amount, zone_k_amount
    from current
),
single as (
    select curvestart from current limit 1
)
-- update the existing "current" with the new "csv"
update trueprice.{m.controlArea}_forwardcurve set
curvestart = newdata.curveStart, -- this reflects the intra update, should only be the time not the date
zone_a_amount = newdata.zone_a_amount, -- mindless update all cols, we don't know which ones updated so try them all
zone_b_amount = newdata.zone_b_amount,
zone_c_amount = newdata.zone_c_amount,
zone_d_amount = newdata.zone_d_amount,
zone_e_amount = newdata.zone_e_amount,
zone_f_amount = newdata.zone_f_amount,
zone_g_amount = newdata.zone_g_amount,
zone_h_amount = newdata.zone_h_amount,
zone_i_amount = newdata.zone_i_amount,
zone_j_amount = newdata.zone_j_amount,
zone_k_amount = newdata.zone_k_amount
from 
    trueprice.{tmp_table_name} as newdata -- our csv data
where 
    trueprice.{m.controlArea}_forwardcurve.strip = newdata.strip 
    and trueprice.{m.controlArea}_forwardcurve.month = newdata.month 
    and trueprice.{m.controlArea}_forwardcurve.curvestart=(select curvestart from single)
'''

# ERCOT
        df.rename(inplace=True, columns={
            'Zone': 'month',  
            'NORTH ZONE':'north_amount',
            'HOUSTON ZONE':'houston_amount',
            'SOUTH ZONE':'south_amount',
            'WEST ZONE':'west_amount'
        })
            backup_query = f'''
with current as (
    -- get the current rows in the database, all of them, not just things that will change
    select id, strip, curvestart, north_amount, houston_amount, south_amount, west_amount from trueprice.{m.controlArea}_forwardcurve where curvestart>='{sod}' and curvestart<='{eod}' and strip='{m.strip}'
),
backup as (
    -- take current rows and insert into database but with a new "curveend" timestamp
    insert into trueprice.{m.controlArea}_forwardcurve_history (id, strip, curvestart, curveend, north_amount, houston_amount, south_amount, west_amount)
    select id, strip, curvestart, '{curveend}' as curveend, north_amount, houston_amount, south_amount, west_amount
    from current
),
single as (
    select curvestart from current limit 1
)
-- update the existing "current" with the new "csv"
--north_amount, houston_amount, south_amount, west_amount
update trueprice.{m.controlArea}_forwardcurve set
curvestart = newdata.curveStart, -- this reflects the intra update, should only be the time not the date
north_amount = newdata.north_amount, -- mindless update all cols, we don't know which ones updated so try them all
houston_amount = newdata.houston_amount,
south_amount = newdata.south_amount,
west_amount = newdata.west_amount
from 
    trueprice.{tmp_table_name} as newdata -- our csv data
where 
    trueprice.{m.controlArea}_forwardcurve.strip = newdata.strip 
    and trueprice.{m.controlArea}_forwardcurve.month = newdata.month 
    and trueprice.{m.controlArea}_forwardcurve.curvestart=(select curvestart from single)
'''
# ISONE
        df.rename(inplace=True, columns={
            'Zone': 'month',
            'MAINE':'maine_amount',
            'NEWHAMPSHIRE': 'newhampshire_amount',
            'VERMONT':'vermont_amount',
            'CONNECTICUT':'connecticut_amount', 
            'RHODEISLAND':'rhodeisland_amount', 
            'SEMASS':'semass_amount', 
            'WCMASS':'wcmass_amount', 
            'NEMASSBOST':'nemassbost_amount', 
            'MASS HUB':'nemassbost_amount'
        })
            backup_query = f'''
with current as (
    -- get the current rows in the database, all of them, not just things that will change
    select id, strip, curvestart, maine_amount, newhampshire_amount, vermont_amount, connecticut_amount, rhodeisland_amount, semass_amount, wcmass_amount, nemassbost_amount, nemassbost_amount from trueprice.{m.controlArea}_forwardcurve where curvestart>='{sod}' and curvestart<='{eod}' and strip='{m.strip}'
),
backup as (
    -- take current rows and insert into database but with a new "curveend" timestamp
    insert into trueprice.{m.controlArea}_forwardcurve_history (id, strip, curvestart, curveend, maine_amount, newhampshire_amount, vermont_amount, connecticut_amount, rhodeisland_amount, semass_amount, wcmass_amount, nemassbost_amount, nemassbost_amount)
    select id, strip, curvestart, '{curveend}' as curveend, maine_amount, newhampshire_amount, vermont_amount, connecticut_amount, rhodeisland_amount, semass_amount, wcmass_amount, nemassbost_amount, nemassbost_amount
    from current
),
single as (
    select curvestart from current limit 1
)
-- update the existing "current" with the new "csv"
update trueprice.{m.controlArea}_forwardcurve set
curvestart = newdata.curveStart, -- this reflects the intra update, should only be the time not the date
maine_amount = newdata.maine_amount, -- mindless update all cols, we don't know which ones updated so try them all
newhampshire_amount = newdata.newhampshire_amount,
vermont_amount = newdata.vermont_amount,
connecticut_amount = newdata.connecticut_amount,
rhodeisland_amount = newdata.rhodeisland_amount,
semass_amount = newdata.semass_amount,
wcmass_amount = newdata.wcmass_amount,
nemassbost_amount = newdata.nemassbost_amount
from 
    trueprice.{tmp_table_name} as newdata -- our csv data
where 
    trueprice.{m.controlArea}_forwardcurve.strip = newdata.strip 
    and trueprice.{m.controlArea}_forwardcurve.month = newdata.month 
    and trueprice.{m.controlArea}_forwardcurve.curvestart=(select curvestart from single)
'''
# MISO
        df.rename(inplace=True, columns={
            'Zone': 'month',
            'AMILCIPS': 'amilcips_amount',
            'AMILCILCO': 'amilcilco_amount',
            'AMILIP': 'amilip_amount',
            'INDY HUB': 'indy_amount'
        })
            backup_query = f'''
with current as (
    -- get the current rows in the database, all of them, not just things that will change
    select id, strip, curvestart, amilcips_amount, amilcilco_amount, amilip_amount, indy_amount from trueprice.{m.controlArea}_forwardcurve where curvestart>='{sod}' and curvestart<='{eod}' and strip='{m.strip}'
),
backup as (
    -- take current rows and insert into database but with a new "curveend" timestamp
    insert into trueprice.{m.controlArea}_forwardcurve_history (id, strip, curvestart, curveend, amilcips_amount, amilcilco_amount, amilip_amount, indy_amount)
    select id, strip, curvestart, '{curveend}' as curveend, amilcips_amount, amilcilco_amount, amilip_amount, indy_amount
    from current
),
single as (
    select curvestart from current limit 1
)
-- update the existing "current" with the new "csv"
update trueprice.{m.controlArea}_forwardcurve set
curvestart = newdata.curveStart, -- this reflects the intra update, should only be the time not the date
amilcips_amount = newdata.amilcips_amount, -- mindless update all cols, we don't know which ones updated so try them all
amilcilco_amount = newdata.amilcilco_amount,
amilip_amount = newdata.amilip_amount,
indy_amount = newdata.indy_amount
from 
    trueprice.{tmp_table_name} as newdata -- our csv data
where 
    trueprice.{m.controlArea}_forwardcurve.strip = newdata.strip 
    and trueprice.{m.controlArea}_forwardcurve.month = newdata.month 
    and trueprice.{m.controlArea}_forwardcurve.curvestart=(select curvestart from single)
'''
# PJM
df.rename(inplace=True, columns={
            'Zone': 'month',
            'AECO':'aeco_amount',
            'AEP':'aep_amount',
            'APS':'aps_amount', 
            'ATSI':'atsi_amount', 
            'BGE':'bge_amount', 
            'COMED':'comed_amount', 
            'DAY':'day_amount', 
            'DEOK':'deok_amount', 
            'DOM':'dom_amount', 
            'DPL':'dpl_amount', 
            'DUQ':'duq_amount', 
            'JCPL':'jcpl_amount', 
            'METED':'meted_amount', 
            'PECO':'peco_amount', 
            'PENELEC':'penelec_amount', 
            'PEPCO':'pepco_amount', 
            'PPL':'ppl_amount', 
            'PSEG':'pseg_amount', 
            'RECO':'reco_amount', 
            'WEST HUB':'west_amount', 
            'AD HUB':'ad_amount', 
            'NI HUB':'ni_amount', 
            'EAST HUB':'east_amount'
          })
            backup_query = f'''
with current as (
    -- get the current rows in the database, all of them, not just things that will change
    select id, strip, curvestart, aeco_amount, aep_amount, aps_amount, atsi_amount, bge_amount, comed_amount, day_amount, deok_amount, dom_amount, dpl_amount, duq_amount, jcpl_amount, meted_amount, peco_amount, penelec_amount, pepco_amount, ppl_amount, pseg_amount, reco_amount, west_amount, ad_amount, ni_amount, east_amount from trueprice.{m.controlArea}_forwardcurve where curvestart>='{sod}' and curvestart<='{eod}' and strip='{m.strip}'
),
backup as (
    -- take current rows and insert into database but with a new "curveend" timestamp
    insert into trueprice.{m.controlArea}_forwardcurve_history (id, strip, curvestart, curveend, aeco_amount, aep_amount, aps_amount, atsi_amount, bge_amount, comed_amount, day_amount, deok_amount, dom_amount, dpl_amount, duq_amount, jcpl_amount, meted_amount, peco_amount, penelec_amount, pepco_amount, ppl_amount, pseg_amount, reco_amount, west_amount, ad_amount, ni_amount, east_amount)
    select id, strip, curvestart, '{curveend}' as curveend, aeco_amount, aep_amount, aps_amount, atsi_amount, bge_amount, comed_amount, day_amount, deok_amount, dom_amount, dpl_amount, duq_amount, jcpl_amount, meted_amount, peco_amount, penelec_amount, pepco_amount, ppl_amount, pseg_amount, reco_amount, west_amount, ad_amount, ni_amount, east_amount
    from current
),
single as (
    select curvestart from current limit 1
)
-- update the existing "current" with the new "csv"
update trueprice.{m.controlArea}_forwardcurve set
curvestart = newdata.curveStart, -- this reflects the intra update, should only be the time not the date
aeco_amount = newdata.aeco_amount,
aep_amount = newdata.aep_amount,
aps_amount = newdata.aps_amount,
atsi_amount = newdata.atsi_amount,
bge_amount = newdata.bge_amount,
comed_amount = newdata.comed_amount,
day_amount = newdata.day_amount,
deok_amount = newdata.deok_amount,
dom_amount = newdata.dom_amount,
dpl_amount = newdata.dpl_amount,
duq_amount = newdata.duq_amount,
jcpl_amount = newdata.jcpl_amount,
meted_amount = newdata.meted_amount,
peco_amount = newdata.peco_amount,
penelec_amount = newdata.penelec_amount,
pepco_amount = newdata.pepco_amount,
ppl_amount = newdata.ppl_amount,
pseg_amount = newdata.pseg_amount,
reco_amount = newdata.reco_amount,
west_amount = newdata.west_amount,
ad_amount = newdata.ad_amount,
ni_amount = newdata.ni_amount,
east_amount = newdata.east_amount
from 
    trueprice.{tmp_table_name} as newdata -- our csv data
where 
    trueprice.{m.controlArea}_forwardcurve.strip = newdata.strip 
    and trueprice.{m.controlArea}_forwardcurve.month = newdata.month 
    and trueprice.{m.controlArea}_forwardcurve.curvestart=(select curvestart from single)
'''