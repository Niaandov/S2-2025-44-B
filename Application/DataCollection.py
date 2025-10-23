import sys, os, datetime
import pandas as pd



class dataCollection:
    def __init__(self):
        self.metricFile = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Results\\metrics.csv")
        self.eventFile = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Results\\events.csv")

        self.currentSessionID = ""
        self.currentParticipantID = ""

        # Check for files existing
        self.createMetricFile()
        self.createEventFile()
        self.getPreviousIDs()



        # I'm not going to fuck around with signals, lovingly, but you can't make me
        self.iTaskRef = None
        self.pTaskRef = None
        self.sTaskRef = None

        self.iResponse = []
        self.pResponse = []
        self.sResponse = []

        self.averageRSorting = 0
        self.averageRInspect = 0
        self.averageRPackage = 0

        self.internalTimer = 0

    

    def setSortingTask(self,task):
        self.sTaskRef = task
    
    def setPackagingTask(self,task):
        self.pTaskRef = task
    
    def setInspectionTask(self,task):
        self.iTaskRef = task

    def updateResponseTime(self, task, response):
        match(task):
            case "sorting":
                self.sResponse.append(response)
                self.averageRSorting = self.getAverageFromArray(self.sResponse) / 1000
                self.writeDictionary(self.createMetricDict("Average Response Time", "Sorting Task", self.averageRSorting, "s"),"metric")

            case "inspection": 
                self.iResponse.append(response)
                self.averageRInspection = self.getAverageFromArray(self.iResponse) / 1000
                self.writeDictionary(self.createMetricDict("Average Response Time", "Inspection Task", self.averageRInspection, "s"),"metric")
            case "packaging":
                self.pResponse.append(response)
                self.averageRPackage= self.getAverageFromArray(self.pResponse) / 1000
                self.writeDictionary(self.createMetricDict("Average Response Time", "Packaging Task", self.averageRPackage, "s"),"metric")

    def getAverageFromArray(self, array):
        total = 0
        length = len(array)
        for i in array:
            total += i 
        
        return total / length



    def retrieveMetrics(self):
        self.internalTimer += 1
        sMetrics = None
        iMetrics = None
        pMetrics = None
        if self.sTaskRef is not None:
            sMetrics = self.sTaskRef.returnData()
            print(sMetrics)
            if sMetrics[1] != 0 and sMetrics[2] != 0:
                sErrorRate = sMetrics[2] / sMetrics[1] * 100
            else:
                sErrorRate = 0

            if sMetrics[1] != 0:    
                sThroughput = sMetrics[1] / self.internalTimer
            else: 
                sThroughput = 0

            if sMetrics[0] != 0:
                if sMetrics[3] != 0:
                    sAccuracy = sMetrics[3] / sMetrics[0]  * 100
                else:
                    sAccuracy = 0
            else:
                sAccuracy = 100
            # Throughput, Error rate, User Accuracy, Corrections
            sMetrics = [sThroughput, sErrorRate, sAccuracy, sMetrics[3], self.averageRSorting]

            self.writeDictionary(self.createMetricDict("Throughput", "Sorting Task", sThroughput, "box / s"),"metric")
            self.writeDictionary(self.createMetricDict("Actual Error Rate", "Sorting Task", sErrorRate, "%"),"metric")
            self.writeDictionary(self.createMetricDict("User Accuracy", "Sorting Task", sAccuracy, "%"),"metric")
            self.writeDictionary(self.createMetricDict("Corrections", "Sorting Task", sMetrics[3], "box"),"metric")


        if self.pTaskRef is not None:
            pMetrics = self.pTaskRef.returnData()
            print(pMetrics)

            if pMetrics[1] != 0:
                pThroughput = pMetrics[1] / self.internalTimer
            else: 
                pThroughput = 0 

            if pMetrics[2] != 0 and pMetrics[1] != 0:
                pErrorRate = pMetrics[2] / pMetrics[1] * 100
            else:
                pErrorRate = 0
            
            if pMetrics[0] != 0:
                if pMetrics[3] != 0:
                    pAccuracy = pMetrics[3] / pMetrics[0]  * 100
                else:
                    pAccuracy = 0
            else: 
                pAccuracy = 100    
            # Throughput, Error rate, User Accuracy, Corrections
            pMetrics = [pThroughput, pErrorRate, pAccuracy, pMetrics[3], self.averageRPackage]

            self.writeDictionary(self.createMetricDict("Throughput", "Packaging Task", pThroughput, "box / s"),"metric")
            self.writeDictionary(self.createMetricDict("Actual Error Rate", "Packaging Task", pErrorRate, "%"),"metric")
            self.writeDictionary(self.createMetricDict("User Accuracy", "Packaging Task", pAccuracy, "%"),"metric")
            self.writeDictionary(self.createMetricDict("Corrections", "Packaging Task", pMetrics[3], "box"),"metric")

        if self.iTaskRef is not None:
            iMetrics = self.iTaskRef.returnData()
            print(iMetrics)
            
            if iMetrics[1] != 0:
                iThroughput = iMetrics[1] / self.internalTimer
            else: 
                iThroughput = 0
            
            if iMetrics[2] != 0 and iMetrics[1] != 0:
                iErrorRate = iMetrics[2] / iMetrics[1] * 100
            else: 
                iErrorRate = 0
            
            if iMetrics[0] != 0:
                if iMetrics[3] != 0:
                    iAccuracy = iMetrics[3] / iMetrics[0]  * 100
                else: 
                    iAccuracy = 0
            else:
                iAccuracy = 100

            # Throughput, Error rate, User Accuracy, Corrections
            iMetrics = [iThroughput, iErrorRate, iAccuracy, iMetrics[3], self.averageRSorting]

            self.writeDictionary(self.createMetricDict("Throughput", "Inspection Task", iThroughput, "box / s"),"metric")
            self.writeDictionary(self.createMetricDict("Actual Error Rate", "Inspection Task", iErrorRate, "%"),"metric")
            self.writeDictionary(self.createMetricDict("User Accuracy", "Inspection Task", iAccuracy, "%"),"metric")
            self.writeDictionary(self.createMetricDict("Corrections", "Inspection Task", iMetrics[3], "box"),"metric")

        return {"sortingTask": sMetrics, "packagingTask": pMetrics, "inspectionTask": iMetrics}

    # Enforced the existence of files if they do not exist
    def createMetricFile(self):
        # Already exists, don't waste time.
        if os.path.exists(self.metricFile):
            return
        # Set up headers.
        df = pd.DataFrame.from_dict({
            "Timestamp": [], 
            "session_id": [],
            "participant_id": [],
            "metric_type": [],
            "task_type": [],
            "value": [],
            "unit": []
        })
        
        df.to_csv(self.metricFile, header=True, index=False)

    def createEventFile(self):
        # Already exists, don't waste time.
        if os.path.exists(self.eventFile):
            return
        # Set up headers.
        df = pd.DataFrame.from_dict({"Timestamp": [], 
            "session_id": [],
            "participant_id": [],
            "event_type": [],
            "task_type": [],
            "details": [],
        })
        
        df.to_csv(self.eventFile, header=True, index=False)
    
    # Gets last participant and session ID from metric file, if any
        # No real reason for metric file in particular, either file works. 
    def getPreviousIDs(self):
        df = pd.read_csv(self.eventFile, usecols=['session_id','participant_id'], encoding="utf8")

        # Make sure we have more than one line, aka we either don't have a prior ID or file is new
        if df["session_id"].count() >= 1:
            self.currentSessionID = df["session_id"].tail(1).values[0]
            self.currentParticipantID = df["participant_id"].tail(1).values[0]

            # Once we have these, we sort of already know that we want to increase them, new session at least. 
            self.newSessionID()

        else:
            # First IDs
            self.currentSessionID = "S001"
            self.currentParticipantID = "P001"


    # Updates Session ID
    def newSessionID(self):
        for s in self.currentSessionID.split("S"):
            if s.isdigit():
                self.currentSessionID = "S" + str(int(s) + 1).zfill(3)

    def setNewParticipantID(self, newIDNum):
        self.currentParticipantID = "S" + str(int(newIDNum) + 1).zfill(3)
                
    def createMetricDict(self, metricType, taskType, value, unit):
        metDict = {
            "Timestamp": [datetime.datetime.now()],
            "session_id": [self.currentSessionID],
            "participant_id": [self.currentParticipantID],
            "metric_type": [metricType],
            "task_type": [taskType],
            "value": [value],
            "unit": [unit]
        }
        return metDict

    def createEventDict(self, eventType, task, details):
        evenDict = {
            "Timestamp": [datetime.datetime.now()],
            "session_id": [self.currentSessionID],
            "participant_id": [self.currentParticipantID],
            "event_type": [eventType],
            "task_type": [task],
            "details": [details]
        }
        return evenDict
    


    # Handles all writes to files
    def writeDictionary(self, dictionary, dataType):
        # Selects appropriate file
        location = ""
        if dataType == "metric":
            location = self.metricFile
        elif dataType == "event":
            location = self.eventFile
        else:
            print("[Data Collection] DataType is invalid or spelt wrong, either 'metric' or 'event'")

        df = pd.DataFrame.from_dict(dictionary)
        df.to_csv(location, mode="a", header=False, index = False)

if __name__ == "__main__":
    fuck = dataCollection()
    fuck.getPreviousIDs()
    fuck.writeDictionary({
            "Timestamp": ["cool"], 
            "session_id": [fuck.currentSessionID],
            "participant_id": [fuck.currentParticipantID],
            "event_type": ["cool one"],
            "task_type": ["mega neat one"],
            "details": ["stop asking questions dipwad"],
    }, "event")


    fuck.newSessionID()
    fuck.writeDictionary({
            "Timestamp": ["cool"], 
            "session_id": [fuck.currentSessionID],
            "participant_id": [fuck.currentParticipantID],
            "event_type": ["cool one"],
            "task_type": ["mega neat one"],
            "details": ["stop asking questions dipwad"],
    }, "event")