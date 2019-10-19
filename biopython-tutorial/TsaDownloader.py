import sys
import re
import time
import threading
import logging
import pandas as pd
import urllib
import urllib.request  as urllib2
from urllib.error import HTTPError


class TsaDownloader:
    
    def __init__(self, **kwargs):
        self.tsaTable = kwargs.get('tsaTable', None)
    
    
    def getResponseCode(self, **kwargs):
        self.url = kwargs.get('url', None)
        
        try:
            conn = urllib.request.urlopen(self.url)
            return conn.getcode()
        
        except HTTPError as e:
            return e.code
    
    
    def logInspector(self, **kwargs):
        self.logPath = kwargs.get('logPath', './logfile.log')
        
        with open(self.logPath, 'r') as lg:
            lines = lg.read().splitlines()
            
            i = 0
            records = []
            self.works = {i: {'datetime': None,'records': None}}
            
            for line in lines:
                
                # identify start information
                startMatch = re.search(r'\[\s([\w-]+\s[\w\:]+),[0-9]+\s-\sINFO\s\] - Work started!$', line)
                if startMatch:
                    self.works[i]['startedIn'] = startMatch.group(1)
                    
                    for line in lines:
                        recordmatch = re.search(r'\sINFO\s\] - Downloading:\s([\w]+)\s', line) #\(size:\s(.+)\)
                        
                        if recordmatch:
                            records.append(recordmatch.group(1))
                            
                    self.works[i]['records'] = records
                    i += 1
                    
        return self.works
    
    
    # INCLUDE A LOG FILE TO CONTROL ALSO DOWNLOADED FILES AND OTHER'S
    def downloadInspector(self):
        df = pd.read_csv(self.tsaTable)
        
        log = self.logInspector()
        
        for k, v in log.items():
            print(k, v['records'])
    
    
    def tsaTableParser(self, **kwargs):
        self.verbose = kwargs.get('verbose', False)
        self.ran = kwargs.get('ran', None) # temporary not used
        self.folder = kwargs.get('folder', './')
        
        df = pd.read_csv(self.tsaTable)
        
        # Gets or creates a logger
        logger = logging.getLogger('__name__')
        
        if not logger.handlers:
            # define file handler and set formatter
            file_handler = logging.FileHandler('logfile.log')
            formatter    = logging.Formatter('[ %(asctime)s - %(levelname)s ] - %(message)s')
            file_handler.setFormatter(formatter)

            # set log level
            logger.setLevel(logging.DEBUG)

            # avoid message propagation to other logger's
            logger.propagate = False

            # add file handler to logger
            logger.addHandler(file_handler)
        
        # start log
        logger.info(
            "Work started!\n"\
            "\n>>>>>>>>>>>>>>>>>>> ------------------------------------ <<<<<<<<<<<<<<<<<<<<<"\
            "\n>>>>>>>>>>>>>>>>>>> --- TSA-TABLE-PARSER-INITIALIZED --- <<<<<<<<<<<<<<<<<<<<<"\
            "\n>>>>>>>>>>>>>>>>>>> ------------------------------------ <<<<<<<<<<<<<<<<<<<<<\n"\
        )
        
        # log stats
        logger.info("Records to be downloaded: %s", len(df))
        
        for x, tsa_code in enumerate(df['prefix_s']):
            
            prefix_match = re.search(r'(^[A-Z]{2})([A-Z]{2})[0-9]+', tsa_code)
            
            # make url
            base_url = "https://sra-download.ncbi.nlm.nih.gov/traces/wgs03/wgs_aux/{}/{}/{}/{}.1.fsa_nt.gz".format(
                    prefix_match.group(1), prefix_match.group(2), tsa_code, tsa_code
            )
            
            if self.verbose:
                print(base_url)
            
            code = self.getResponseCode(url=base_url)
            
            if code == 200:
                
                # make location to save file
                save_url = '{}/{}.1.fsa_nt.gz'.format(self.folder, tsa_code)
                
                # retrieve object size
                req = urllib.request.urlopen(base_url)
                objSize = req.info()['Content-Length']
                
                # log tsa_code and start time
                start = time.clock()
                logger.info(
                    'Downloading record %s: %s (size: %.2fM)', 
                    x + 1, tsa_code, int(objSize) / 1e+6
                )
                
                urllib.request.urlretrieve(base_url, save_url)
                #req.retrieve(base_url, save_url)
                
                logger.info('Download %s finished (elapsed time: %.3f)', tsa_code, time.clock() - start)
                
                if self.verbose:
                    print(tsa_code + ' saved in ' + save_url)
                
            else:
                print(tsa_code + 'not found')
                next
        
        logger.info('Work finished!\n')

