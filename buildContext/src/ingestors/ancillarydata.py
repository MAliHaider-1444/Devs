"""
Implements the Slowly Changed Dimensions to insert the data into database
"""
import datetime
import pandas as pd
from database_conection import ConnectDatabase


class AncillaryData:
    """
    constructor which will makes the connection to the database
    """
    
    def __init__(self):
        """
        makes the 
        """
        data_base = ConnectDatabase()
        self.engine = data_base.get_engine()

    def ingestion(self, data):
        """
        Handling Ingestion for ancillarydata
        """

        df = pd.read_csv(data.fileName, parse_dates=['Month'])
        df.rename(inplace=True, columns={
            'Zone ID': 'zone_id',
            'Load Zone': 'load_zone',
            'Month': 'month',
            'RTLO ($/MWh)': 'rtlo_mwh',
            'DALO ($/MWh)': 'dalo_mwh',
            'Deviations ($/MWh)': 'deviations_mwh',
            'NCP ($/MW)': 'ncp_mw'
        })

        df.drop(columns=["zone_id"], inplace=True)

        df.insert(0, 'strip', data.strip) # stored as object, don't freak on dtypes
        df.insert(0, 'curvestart', data.curveStart) # date on file, not the internal zone/month column
        

        sod = data.curveStart.strftime('%Y-%m-%d') # drop time, since any update should be new
        now = data.curveStart
        eod = (data.curveStart + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        check_query = f"""
            -- if nothing found, new data, insert it, or do one of these
            
            select exists(select 1 from trueprice.{data.controlArea}_ancillarydata where curvestart='{now}'and strip='{data.strip}') -- ignore, db == file based on timestamp
            UNION ALL
            select exists(select 1 from trueprice.{data.controlArea}_ancillarydata where curvestart>='{sod}' and curvestart<'{now}' and strip='{data.strip}') -- update, db is older
            UNION ALL
            select exists(select 1 from trueprice.{data.controlArea}_ancillarydata where curvestart>'{now}' and curvestart<'{eod}' and strip='{data.strip}') -- ignore, db is newer
        """
        query_result = pd.read_sql(check_query, self.engine)
        same, old_exists, new_exists = query_result.exists[0], query_result.exists[1], query_result.exists[2]

        if same: # if data already exists neglect it
            return "Data already exists based on timestamp and strip"
        
        elif not same and not new_exists and not old_exists: # if data is new then insert it
            r = df.to_sql(f"{data.controlArea}_ancillarydata", con = self.engine, if_exists = 'append', chunksize=1000, schema="trueprice", index=False)
            if r is None:
                return "Failed to insert"            

        elif old_exists: # if there exists old data, handle it with slowly changing dimensions
            tmp_table_name = f"{data.controlArea}_ancillarydata_{data.snake_timestamp()}" # temp table to hold new csv data so we can work in SQL
            r = df.to_sql(f'{tmp_table_name}', con = self.engine, if_exists = 'replace', chunksize=1000, schema="trueprice", index=False)
            if r is None:
                return "Unable to create data"

            with self.engine.connect() as con:
                curveend = data.curveStart # the new data ends the old data
                backup_query = ''''''
                if data.controlArea == "isone":
                    backup_query = f'''
                        with current as (
                            -- get the current rows in the database, all of them, not just things that will change

                            select id, strip, curvestart, load_zone, rtlo_mwh, dalo_mwh, deviations_mwh, ncp_mw from trueprice.{data.controlArea}_ancillarydata where curvestart>='{sod}' and curvestart<='{eod}' and strip='{data.strip}'
                        ),
                        backup as (
                            -- take current rows and insert into database but with a new "curveend" timestamp

                            insert into trueprice.{data.controlArea}_ancillarydata_history (id, strip, curvestart, curveend, load_zone, rtlo_mwh, dalo_mwh, deviations_mwh, ncp_mw)
                            select id, strip, curvestart, '{curveend}' as curveend, load_zone, rtlo_mwh, dalo_mwh, deviations_mwh, ncp_mw
                            from current
                        ),
                        single as (
                            select curvestart from current limit 1
                        )
                        -- update the existing "current" with the new "csv"

                        update trueprice.{data.controlArea}_ancillarydata set
                        curvestart = newdata.curveStart, -- this reflects the intra update, should only be the time not the date
                        load_zone = newdata.load_zone, -- mindless update all cols, we don't know which ones updated so try them all
                        rtlo_mwh = newdata.rtlo_mwh,
                        dalo_mwh = newdata.dalo_mwh,
                        deviations_mwh = newdata.deviations_mwh,
                        ncp_mw = newdata.ncp_mw
                        from 
                            trueprice.{tmp_table_name} as newdata -- our csv data
                        where 
                            trueprice.{data.controlArea}_ancillarydata.strip = newdata.strip 
                            and trueprice.{data.controlArea}_ancillarydata.month = newdata.month 
                            and trueprice.{data.controlArea}_ancillarydata.curvestart=(select curvestart from single)
                    '''        
                #elif m.controlArea == "nyiso":
                # etc.
                else:
                    return "Unknown update,abort"
                
                # finally execute the query
                r = con.execute(backup_query)            
                con.execute(f"drop table trueprice.{tmp_table_name}")

        elif new_exists:
            return "Newer data in database, abort"
        else:
            return "Ingestion logic error, we should not be here"