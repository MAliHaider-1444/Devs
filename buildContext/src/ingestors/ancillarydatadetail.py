

# STATUS
# need to know which columns make the row unique so we can do the update, we can't use month/strip here because they don't change

"""
Implements the Slowly Changed Dimensions to insert the data into database
"""

import pandas as pd
import datetime
from database_conection import ConnectDatabase

class AncillaryDataDetails:
    """
    constructor which will makes the connection to the database
    """
    
    def __init__(self):
        """
        makes the 
        """
        data_base = ConnectDatabase()
        self.engine = data_base.get_engine()

    #Zone ID,Ancillary,Load Zone,Month,Price,Billing Determinant,,,,

    def ingestion(self, data):
        df = pd.read_csv(data.fileName, parse_dates=['Month'])
        df.dropna(inplace=True, axis="columns")
        df.rename(inplace=True, columns={
            'Zone ID': 'zone_id',
            'Ancillary': 'ancillary',
            'Load Zone': 'load_zone',
            'Month': 'month',
            'Price': 'price',
            'Billing Determinant': 'billing_determinant'
        })

        df.drop(columns=["zone_id"], inplace=True)

        df.insert(0, 'strip', data.strip) # stored as object, don't freak on dtypes
        df.insert(0, 'curvestart', data.curveStart) # date on file, not the internal zone/month column

        
        sod = data.curveStart.strftime('%Y-%m-%d') # drop time, since any update should be new
        now = data.curveStart
        eod = (data.curveStart + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        check_query = f"""
            -- if nothing found, new data, insert it, or do one of these
            
            select exists(select 1 from trueprice.{data.controlArea}_ancillarydatadetails where curvestart='{now}'and strip='{data.strip}') -- ignore, db == file based on timestamp
            UNION ALL
            select exists(select 1 from trueprice.{data.controlArea}_ancillarydatadetails where curvestart>='{sod}' and curvestart<'{now}' and strip='{data.strip}') -- update, db is older
            UNION ALL
            select exists(select 1 from trueprice.{data.controlArea}_ancillarydatadetails where curvestart>'{now}' and curvestart<'{eod}' and strip='{data.strip}') -- ignore, db is newer
        """
        r = pd.read_sql(check_query, self.engine)
        same, old_exists, new_exists = r.exists[0], r.exists[1], r.exists[2]

        if same: # if data already exists neglect it
            return "Data already exists based on timestamp and strip"
        
        elif not same and not new_exists and not old_exists:
            r = df.to_sql(f"{data.controlArea}_ancillarydatadetails", con = self.engine, if_exists = 'append', chunksize=1000, schema="trueprice", index=False)
            if r is None:
                return "Failed to insert"
            
        elif old_exists: # if there exists old data, handle it with slowly changing dimensions
            tmp_table_name = f"{data.controlArea}_ancillarydatadetails_{data.snake_timestamp()}" # temp table to hold new csv data so we can work in SQL
            r = df.to_sql(f'{tmp_table_name}', con = self.engine, if_exists = 'replace', chunksize=1000, schema="trueprice", index=False)
            if r is None:
                return "Failed to insert"

            with self.engine.connect() as con:
                curveend = data.curveStart # the new data ends the old data
                backup_query = ''''''
                if data.controlArea == "isone":
                    backup_query = f'''
                        with current as (
                            -- get the current rows in the database, all of them, not just things that will change
                            select id, strip, curvestart, load_zone, ancillary, month, price, billing_determinant from trueprice.{data.controlArea}_ancillarydatadetails where curvestart>='{sod}' and curvestart<='{eod}' and strip='{data.strip}'
                        ),
                        backup as (
                            -- take current rows and insert into database but with a new "curveend" timestamp
                            insert into trueprice.{data.controlArea}_ancillarydatadetails_history (id, strip, curvestart, curveend, load_zone, ancillary, month, price, billing_determinant)
                            select id, strip, curvestart, '{curveend}' as curveend, load_zone, ancillary, month, price, billing_determinant
                            from current
                        ),
                        single as (
                            select curvestart from current limit 1
                        )
                        -- update the existing "current" with the new "csv"
                        update trueprice.{data.controlArea}_ancillarydatadetails set
                        curvestart = newdata.curveStart, -- this reflects the intra update, should only be the time not the date
                        load_zone = newdata.load_zone, -- mindless update all cols, we don't know which ones updated so try them all
                        ancillary = newdata.ancillary,
                        price = newdata.price,
                        billing_determinant = newdata.billing_determinant
                        from 
                            trueprice.{tmp_table_name} as newdata -- our csv data
                        where 
                            trueprice.{data.controlArea}_ancillarydatadetails.strip = newdata.strip 
                            and trueprice.{data.controlArea}_ancillarydatadetails.month = newdata.month 
                            and trueprice.{data.controlArea}_ancillarydatadetails.curvestart=(select curvestart from single)
                    
                    '''        
                #elif m.controlArea == "nyiso":
                # etc.
                else:
                    return "Unknown update,abort"
                    
                r = con.execute(backup_query)            
                con.execute(f"drop table trueprice.{tmp_table_name}")

        elif new_exists:
            return "Newer data in database, abort"
        else:
            return "Ingestion logic error, we should not be here"