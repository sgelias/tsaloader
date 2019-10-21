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
        objSizeStats = []
        
        # Gets or creates a logger
        logger = logging.getLogger('__name__')
        
        if not logger.handlers:
            # define file handler and set formatter
            file_handler = logging.FileHandler('logfile.log', mode = 'w')
            formatter    = logging.Formatter('[ %(asctime)s - %(levelname)s ] %(message)s')
            file_handler.setFormatter(formatter)

            # set log level
            logger.setLevel(logging.DEBUG)

            # avoid message propagation to other logger's
            logger.propagate = False

            # add file handler to logger
            logger.addHandler(file_handler)
        
        # start log
        logger.info(
            "WORK STARTED!\n"\
            "\n>>>>>>>>>>>>>>>>>>> ------------------------------------ <<<<<<<<<<<<<<<<<<<"\
            "\n>>>>>>>>>>>>>>>>>>> --- TSA-TABLE-PARSER-INITIALIZED --- <<<<<<<<<<<<<<<<<<<"\
            "\n>>>>>>>>>>>>>>>>>>> ------------------------------------ <<<<<<<<<<<<<<<<<<<\n"\
        )
        
        # log stats
        logger.info("Records to be downloaded: %s\n", len(df))
        
        for x, tsa_code in enumerate(df['prefix_s']):
            
            prefix_match = re.search(r'(^[A-Z]{2})([A-Z]{2})[0-9]+', tsa_code)
            
            # make url
            base_url = "https://sra-download.ncbi.nlm.nih.gov/traces/wgs03/wgs_aux/{}/{}/{}/{}.1.fsa_nt.gz".format(
                    prefix_match.group(1), prefix_match.group(2), tsa_code, tsa_code
            )
            
            if self.verbose:
                print(base_url)
            
            code = self.getResponseCode(url=base_url)
            print(code)
            
            if code == 200:
                
                # make location to save file
                save_url = '{}/{}.1.fsa_nt.gz'.format(self.folder, tsa_code)
                
                # retrieve object info
                req = urllib.request.urlopen(base_url)
                objSize = req.info()['Content-Length']
                
                # populate objSize for stats
                objSizeStats.append(int(objSize))
                
                # log tsa_code and start time
                start = time.clock()
                logger.info(
                    'Downloading record %s: %s (size: %.2fM)', 
                    x + 1, tsa_code, int(objSize) / 1e+6
                )
                
                # download file
                #urllib.request.urlretrieve(base_url, save_url)
                
                logger.info(
                    '-- finished (elapsed time: %.3f)', 
                    time.clock() - start
                )
                
                logger.info(
                    "-- stats (Mb): TOTAL %.3f - MIN %.4f - MEDIAN %.4f - MAX %.4f\n",
                    sum(objSizeStats) / 1e+6, 
                    min(objSizeStats) / 1e+6, 
                    statistics.median(objSizeStats) / 1e+6, 
                    max(objSizeStats) / 1e+6
                )
                
                if self.verbose:
                    print(tsa_code + ' saved in ' + save_url)
                
            else:
                print(tsa_code + 'not found')
                next
        
        logger.info('WORK FINISHED!\n')
    
    
    def logInspector(self, **kwargs):
        self.logPath = kwargs.get('logPath', './logfile.log')
        
        with open(self.logPath, 'r') as lg:
            lines = lg.readlines()
            lastLine = lines[-1]
        
        with open(self.logPath, 'r') as lg:
            
            print(lastLine)
            
            i = 0
            records = []
            self.out = {}
            
            for x, line in enumerate(lg):
                
                # initializa works
                work = []
                #work = {'startedIn': None,'records': []}
                
                # match for start
                startMatch = re.search(
                    r'^\[\s([\w-]+\s[\w\:]+),[0-9]+\s-\sINFO\s\] WORK STARTED!$', line
                )
                if startMatch:
                    
                    # define 'startedIn'
                    startedIn = startMatch.group(1)
                    
                    # initialize previous line
                    previousLine = False
                    for y, line in enumerate(lg):
                        
                        # match for record
                        recordMatch = re.search(
                            r"^\[\s[\w-]+\s[\w\:]+,[0-9]+\s-\sINFO\s\]"\
                            "\sDownloading record\s[0-9]+:\s([\w]+)\s(\(.+\))$", line
                        )
                        recordFinishMatch = re.search(
                            r"^\[\s[\w-]+\s[\w\:]+,[0-9]+\s-\sINFO\s\]"\
                            "\s-- finished\s\(.+\)$", line
                        )
                        #if recordMatch:
                        #    print(1)
                        #    previousLine = recordMatch.group(1)
                        #    next
                        
                        if recordMatch:
                            work.append((startedIn, recordMatch.group(1),'unfinished'))
                            self.out[i] = work
                            previousLine = True
                            print(work)
                            break
                        
                        if recordFinishMatch and previousLine:
                            work[-1] = (startedIn, recordMatch.group(1),'finished')
                            self.out[i] = work
                            print(work)
                            
                            previousLine = False
                            next
                        
                        # match for finish
                        workFinishMatch = re.search(
                            r'^\[\s([\w-]+\s[\w\:]+),[0-9]+\s-\sINFO\s\] WORK FINISHED!$', line
                        )
                        if workFinishMatch:
                            self.out[i] = work
                            i += 1
                            break
                    
        return self.out
    