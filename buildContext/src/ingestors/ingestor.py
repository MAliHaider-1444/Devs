import re
import os
import datetime
from ingestors.ancillarydata import AncillaryData
from ingestors.ancillarydatadetail import AncillaryDataDetails
from ingestors.energy import EnergyData
from ingestors.rec import RecData 

class ParseError(Exception):
    pass

class ExistingDataError(Exception):
    pass

class SQLError(Exception):
    pass


class Ingestion:
    def __init__(self):
        self.anci_data = AncillaryData()
        self.anci_data_detail = AncillaryDataDetails()
        self.eng_data = EnergyData()
        self.rec_data = RecData()

    def validate(self, file_name):
        """
        validates the incoming data file name
        """
        file_name_components_pattern = re.compile(".*/(.+?)_(.+?)_(.+?)_(.+?)_(.+)?.csv$") # len(5-6)
        
        matched = file_name_components_pattern.search(file_name)
        if matched == None:
            return ParseError(f"failed to parse {file_name} - regex")
        
        results = matched.groups()
        if len(results) != 5: # todo - confirm works with and without "_cob" extension in name
            return ParseError(f"failed to parse {file_name} - component count")

        # controlArea == iso
        # issue == curveTime
        (curveType, controlArea, strip, curveDate, issue) = results    
        curveType = os.path.basename(curveType).replace("Curve","")

        # todo - should error if timestamp/date is missing or invalid instead of trying to fix here, so remove this block
        # add default value here for time, maybe not worth it, need to see how it flows
        timeComponent = None
        if issue is None:    
            timeComponent = "000000"
        else:
            timeStamp = issue[1:] # drop leading underscore; else fix regex above
            if timeStamp == "cob":
                timeComponent = "235959" # 24h clock, convert to last possible second so we can sort properly
            elif int(timeStamp):
                timeComponent = timeStamp
            else:
                return ParseError(f"failed to parse {file_name} - time component")

        timestamp = datetime.datetime.strptime(curveDate+timeComponent, "%Y%m%d%H%M%S")
        return TLE_Meta(file_name, curveType, controlArea, strip, timestamp)
    

    def process(self, files, steps):
        """
        Performs the validation 
        """
        meta = None

        # validate
        valid = []
        for f in files:
            meta = steps["v"](f)
            if meta is None or isinstance(meta, ParseError):
                return meta # all files must pass, in case systematic errors
            else:
                valid.append(meta)

        # todo - storage to s3
        # add sha later
        for m in valid:
            result = steps["s"](m) # store before we place in db
            if result is not None :
                return result

        # insert db / api check each as we go (need to find way to redo/short-circuit/single file, etc.)
        for m in valid:
            result = steps["i"](m) # insert/update db
            if result is not None:
                return result
            result = steps["va"](m) # validate data made it to db via api
            if result is not None:
                return result

        return None
    
    # todo - s3
    def storage(file_name):
        """
        store the data to s3 bucket
        """
        pass

    def validate_api(file_name):
        """
        validate api request
        """
        None


    def call_ingestor(self,file):
        """
        performing several operations based on the file type
        """

        files = [file]
        result = None
        if re.search("forward", file, re.IGNORECASE):
            result = self.process(files, {"validate_data":self.validate, "storage":self.storage, "ingestion":self.eng_data.ingestion, "validate_api": self.validate_api})
        elif re.search("ancillarydatadetails", file, re.IGNORECASE):
            result = self.process(files, {"validate_data":self.validate, "storage":self.storage, "ingestion":self.anci_data_detail.ingestion, "validate_api": self.validate_api})
        elif re.search("ancillarydata", file, re.IGNORECASE):
            result = self.process(files, {"validate_data":self.validate, "storage":self.storage, "ingestion":self.anci_data.ingestion, "validate_api": self.validate_api})
        else:
            print("Shouldn't be here")
            return

        if result is not None:
            print(f"Ingestion Failed: {result}")
        else:
            print("Ingestion Succeeded")

        print("Finished Ingestion")


class TLE_Meta:
    def __init__(self, fileName, curveType, controlArea, strip, curveTimestamp):
        self.fileName = fileName
        self.curveType = curveType.lower()
        self.controlArea = controlArea.lower()
        self.strip = strip.lower()
        self.curveStart = curveTimestamp
    
    def snake_timestamp(self):
        return self.curveStart.strftime("%Y_%m_%d_%H_%M_%S")