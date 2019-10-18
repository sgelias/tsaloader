class TsaDownloader:
    
    def __init__(self, **kwargs):
        self.tsaTable = kwargs.get('tsaTable', None)
        #self.tsaTable = tsaTable
    
    def getResponseCode(self, **url):
        self.url = url.get('url', None)
        try:
            conn = urllib.request.urlopen(self.url)
            return conn.getcode()
        except HTTPError as e:
            return e.code
    
    def tsaTableParser(self, **kwargs):
        self.ran = kwargs.get('ran', None)
        self.folder = kwargs.get('folder', './')
        df = pd.read_csv(self.tsaTable)
        
        for tsa_code in df['prefix_s']:
            
            prefix_s = tsa_code
            prefix_match = re.search(r'(^[A-Z]{2})([A-Z]{2})[0-9]+', prefix_s)
            
            # make url
            base_url = 'https://sra-download.ncbi.nlm.nih.gov/traces/wgs03/wgs_aux/{}/{}/{}/{}.1.fsa_nt.gz'.format(
                prefix_match.group(1), prefix_match.group(2), prefix_s, prefix_s)
            print(base_url)
            
            code = getResponseCode(base_url)
            
            if code == 200:
                save_url = '{}/{}.1.fsa_nt.gz'.format(self.folder, prefix_s)
                req = urllib.request.URLopener()
                req.retrieve(base_url, save_url)
                print(prefix_s + 'saved in ' + save_url)
                
            else:
                print(prefix_s + 'not found')
                next
                
            
        
        #return df
