"""
Implements the Slowly Changed Dimensions to insert the data into database
"""

import pandas as pd
from database_conection import ConnectDatabase
class RecData:
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