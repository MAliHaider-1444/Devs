"""
Implements the Slowly Changed Dimensions to insert the data into database
"""
import datetime
import pandas as pd
from database_conection import ConnectDatabase

class EnergyData:
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

        # WARNING the provided CSV has many empty rows which are not skipped because they are empty strings
        date_cols = ['Zone']
        df = pd.read_csv(data.fileName, header=[2], skiprows=(3,3), dtype={
            'Zone': str, # Bad CSV header (should be curveStart or Month)
        }, parse_dates=date_cols).dropna() # acts as context manager
        
        df[df.columns[1:]] = df[df.columns[1:]].replace('[\$,]', '', regex=True).astype(float) # see warning on Float64Dtype, this removes money and converts to float

        if data.controlArea == "nyiso":
            df.rename(inplace=True, columns={
                'Zone': 'month',
                'ZONE A': 'zone_a_amount',
                'ZONE B': 'zone_b_amount',
                'ZONE C': 'zone_c_amount',
                'ZONE D': 'zone_d_amount',
                'ZONE E': 'zone_e_amount',
                'ZONE F': 'zone_f_amount',
                'ZONE G': 'zone_g_amount',
                'ZONE H': 'zone_h_amount',
                'ZONE I': 'zone_i_amount',
                'ZONE J': 'zone_j_amount',
                'ZONE K': 'zone_k_amount'
                })
        elif data.controlArea == "miso":
            df.rename(inplace=True, columns={
                'Zone': 'month',
                'AMILCIPS': 'amilcips_amount',
                'AMILCILCO': 'amilcilco_amount',
                'AMILIP': 'amilip_amount',
                'INDY HUB': 'indy_amount'
            })
        elif data.controlArea == "ercot":
            df.rename(inplace=True, columns={
                'Zone': 'month',  
                'NORTH ZONE':'north_amount',
                'HOUSTON ZONE':'houston_amount',
                'SOUTH ZONE':'south_amount',
                'WEST ZONE':'west_amount'
            })
        elif data.controlArea == "pjm":
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
        elif data.controlArea == "isone":
            #Zone,MAINE,NEWHAMPSHIRE,VERMONT,CONNECTICUT,RHODEISLAND,SEMASS,WCMASS,NEMASSBOST,MASS HUB
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
                'MASS HUB':'mass_amount'
            })
        else:
            return # error

        df.insert(0, 'strip', data.strip) # stored as object, don't freak on dtypes
        df.insert(0, 'curvestart', data.curveStart) # date on file, not the internal zone/month column


        # using exists always return true or false versus empty/None
        sod = data.curveStart.strftime('%Y-%m-%d') # drop time, since any update should be new
        now = data.curveStart
        eod = (data.curveStart + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        

        check_query = f"""
            -- if nothing found, new data, insert it, or do one of these
        
            select exists(select 1 from trueprice.{data.controlArea}_forwardcurve where curvestart='{now}'and strip='{data.strip}') -- ignore, db == file based on timestamp
            UNION ALL
            select exists(select 1 from trueprice.{data.controlArea}_forwardcurve where curvestart>='{sod}' and curvestart<'{now}' and strip='{data.strip}') -- update, db is older
            UNION ALL
            select exists(select 1 from trueprice.{data.controlArea}_forwardcurve where curvestart>'{now}' and curvestart<'{eod}' and strip='{data.strip}') -- ignore, db is newer
        """
        r = pd.read_sql(check_query, self.engine)
        same, old_exists, new_exists = r.exists[0], r.exists[1], r.exists[2]

        if same: # if data already exists neglect it
            return "Data already exists based on timestamp and strip"
        
        elif not same and not new_exists and not old_exists: # if data is new then insert it
            r = df.to_sql(f"{data.controlArea}_forwardcurve", con = self.engine, if_exists = 'append', chunksize=1000, schema="trueprice", index=False)
            if r is None:
                if r is None:
                    return "Failed to insert" 
                
        elif old_exists: # if there exists old data, handle it with slowly changing dimensions
            tmp_table_name = f"{data.controlArea}_forwardcurve_{data.snake_timestamp()}" # temp table to hold new csv data so we can work in SQL
            r = df.to_sql(f'{tmp_table_name}', con = self.engine, if_exists = 'replace', chunksize=1000, schema="trueprice", index=False)
            if r is None:
                return "Unable to create data"

            # history/update
            with self.engine.connect() as con:
                curveend = data.curveStart # the new data ends the old data
                backup_query = ''''''
                if data.controlArea == "nyiso":
                    backup_query = f'''
                        with current as (
                            -- get the current rows in the database, all of them, not just things that will change
                            select id, strip, curvestart, zone_a_amount, zone_b_amount, zone_c_amount, zone_d_amount, zone_e_amount, zone_f_amount, zone_g_amount, zone_h_amount, zone_i_amount, zone_j_amount, zone_k_amount from trueprice.{data.controlArea}_forwardcurve where curvestart>='{sod}' and curvestart<='{eod}' and strip='{data.strip}'
                        ),
                        backup as (
                            -- take current rows and insert into database but with a new "curveend" timestamp
                            insert into trueprice.{data.controlArea}_forwardcurve_history (id, strip, curvestart, curveend, zone_a_amount, zone_b_amount, zone_c_amount, zone_d_amount, zone_e_amount, zone_f_amount, zone_g_amount, zone_h_amount, zone_i_amount, zone_j_amount, zone_k_amount)
                            select id, strip, curvestart, '{curveend}' as curveend, zone_a_amount, zone_b_amount, zone_c_amount, zone_d_amount, zone_e_amount, zone_f_amount, zone_g_amount, zone_h_amount, zone_i_amount, zone_j_amount, zone_k_amount
                            from current
                        ),
                        single as (
                            select curvestart from current limit 1
                        )
                        -- update the existing "current" with the new "csv"
                        update trueprice.{data.controlArea}_forwardcurve set
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
                            trueprice.{data.controlArea}_forwardcurve.strip = newdata.strip 
                            and trueprice.{data.controlArea}_forwardcurve.month = newdata.month 
                            and trueprice.{data.controlArea}_forwardcurve.curvestart=(select curvestart from single)
                    '''
                
                elif data.controlArea == "miso":
                    backup_query = f'''
                        with current as (
                            -- get the current rows in the database, all of them, not just things that will change
                            select id, strip, curvestart, amilcips_amount, amilcilco_amount, amilip_amount, indy_amount from trueprice.{data.controlArea}_forwardcurve where curvestart>='{sod}' and curvestart<='{eod}' and strip='{data.strip}'
                        ),
                        backup as (
                            -- take current rows and insert into database but with a new "curveend" timestamp
                            insert into trueprice.{data.controlArea}_forwardcurve_history (id, strip, curvestart, curveend, amilcips_amount, amilcilco_amount, amilip_amount, indy_amount)
                            select id, strip, curvestart, '{curveend}' as curveend, amilcips_amount, amilcilco_amount, amilip_amount, indy_amount
                            from current
                        ),
                        single as (
                            select curvestart from current limit 1
                        )
                        -- update the existing "current" with the new "csv"
                        update trueprice.{data.controlArea}_forwardcurve set
                        curvestart = newdata.curveStart, -- this reflects the intra update, should only be the time not the date
                        amilcips_amount = newdata.amilcips_amount, -- mindless update all cols, we don't know which ones updated so try them all
                        amilcilco_amount = newdata.amilcilco_amount,
                        amilip_amount = newdata.amilip_amount,
                        indy_amount = newdata.indy_amount
                        from 
                            trueprice.{tmp_table_name} as newdata -- our csv data
                        where 
                            trueprice.{data.controlArea}_forwardcurve.strip = newdata.strip 
                            and trueprice.{data.controlArea}_forwardcurve.month = newdata.month 
                            and trueprice.{data.controlArea}_forwardcurve.curvestart=(select curvestart from single)
                    '''    

                elif data.controlArea == "ercot":
                    backup_query = f'''
                        with current as (
                            -- get the current rows in the database, all of them, not just things that will change
                            select id, strip, curvestart, north_amount, houston_amount, south_amount, west_amount from trueprice.{data.controlArea}_forwardcurve where curvestart>='{sod}' and curvestart<='{eod}' and strip='{data.strip}'
                        ),
                        backup as (
                            -- take current rows and insert into database but with a new "curveend" timestamp
                            insert into trueprice.{data.controlArea}_forwardcurve_history (id, strip, curvestart, curveend, north_amount, houston_amount, south_amount, west_amount)
                            select id, strip, curvestart, '{curveend}' as curveend, north_amount, houston_amount, south_amount, west_amount
                            from current
                        ),
                        single as (
                            select curvestart from current limit 1
                        )
                        -- update the existing "current" with the new "csv"
                        --north_amount, houston_amount, south_amount, west_amount
                        update trueprice.{data.controlArea}_forwardcurve set
                        curvestart = newdata.curveStart, -- this reflects the intra update, should only be the time not the date
                        north_amount = newdata.north_amount, -- mindless update all cols, we don't know which ones updated so try them all
                        houston_amount = newdata.houston_amount,
                        south_amount = newdata.south_amount,
                        west_amount = newdata.west_amount
                        from 
                            trueprice.{tmp_table_name} as newdata -- our csv data
                        where 
                            trueprice.{data.controlArea}_forwardcurve.strip = newdata.strip 
                            and trueprice.{data.controlArea}_forwardcurve.month = newdata.month 
                            and trueprice.{data.controlArea}_forwardcurve.curvestart=(select curvestart from single)
                    '''                
                
                
                elif data.controlArea == "pjm":
                    backup_query = f'''
                        with current as (
                            -- get the current rows in the database, all of them, not just things that will change
                            select id, strip, curvestart, aeco_amount, aep_amount, aps_amount, atsi_amount, bge_amount, comed_amount, day_amount, deok_amount, dom_amount, dpl_amount, duq_amount, jcpl_amount, meted_amount, peco_amount, penelec_amount, pepco_amount, ppl_amount, pseg_amount, reco_amount, west_amount, ad_amount, ni_amount, east_amount from trueprice.{data.controlArea}_forwardcurve where curvestart>='{sod}' and curvestart<='{eod}' and strip='{data.strip}'
                        ),
                        backup as (
                            -- take current rows and insert into database but with a new "curveend" timestamp
                            insert into trueprice.{data.controlArea}_forwardcurve_history (id, strip, curvestart, curveend, aeco_amount, aep_amount, aps_amount, atsi_amount, bge_amount, comed_amount, day_amount, deok_amount, dom_amount, dpl_amount, duq_amount, jcpl_amount, meted_amount, peco_amount, penelec_amount, pepco_amount, ppl_amount, pseg_amount, reco_amount, west_amount, ad_amount, ni_amount, east_amount)
                            select id, strip, curvestart, '{curveend}' as curveend, aeco_amount, aep_amount, aps_amount, atsi_amount, bge_amount, comed_amount, day_amount, deok_amount, dom_amount, dpl_amount, duq_amount, jcpl_amount, meted_amount, peco_amount, penelec_amount, pepco_amount, ppl_amount, pseg_amount, reco_amount, west_amount, ad_amount, ni_amount, east_amount
                            from current
                        ),
                        single as (
                            select curvestart from current limit 1
                        )
                        -- update the existing "current" with the new "csv"
                        update trueprice.{data.controlArea}_forwardcurve set
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
                            trueprice.{data.controlArea}_forwardcurve.strip = newdata.strip 
                            and trueprice.{data.controlArea}_forwardcurve.month = newdata.month 
                            and trueprice.{data.controlArea}_forwardcurve.curvestart=(select curvestart from single)
                    '''

                elif data.controlArea == "isone":
                    backup_query = f'''
                        with current as (
                            -- get the current rows in the database, all of them, not just things that will change
                            select id, strip, curvestart, maine_amount, newhampshire_amount, vermont_amount, connecticut_amount, rhodeisland_amount, semass_amount, wcmass_amount, nemassbost_amount, nemassbost_amount from trueprice.{data.controlArea}_forwardcurve where curvestart>='{sod}' and curvestart<='{eod}' and strip='{data.strip}'
                        ),
                        backup as (
                            -- take current rows and insert into database but with a new "curveend" timestamp
                            insert into trueprice.{data.controlArea}_forwardcurve_history (id, strip, curvestart, curveend, maine_amount, newhampshire_amount, vermont_amount, connecticut_amount, rhodeisland_amount, semass_amount, wcmass_amount, nemassbost_amount, nemassbost_amount)
                            select id, strip, curvestart, '{curveend}' as curveend, maine_amount, newhampshire_amount, vermont_amount, connecticut_amount, rhodeisland_amount, semass_amount, wcmass_amount, nemassbost_amount, nemassbost_amount
                            from current
                        ),
                        single as (
                            select curvestart from current limit 1
                        )
                        -- update the existing "current" with the new "csv"
                        update trueprice.{data.controlArea}_forwardcurve set
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
                            trueprice.{data.controlArea}_forwardcurve.strip = newdata.strip 
                            and trueprice.{data.controlArea}_forwardcurve.month = newdata.month 
                            and trueprice.{data.controlArea}_forwardcurve.curvestart=(select curvestart from single)
                    '''
                else:
                    return "Unknown update,abort"
                
                # finally execute the query
                r = con.execute(backup_query)            
                con.execute(f"drop table trueprice.{tmp_table_name}")

        elif new_exists:
            return "Newer data in database, abort"
        else:
            return "Ingestion logic error, we should not be here"