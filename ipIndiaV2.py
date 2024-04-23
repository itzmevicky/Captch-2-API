__VERSION__ ='Ip-India Link 2 Extractor, AI Edition.'
__DEVELOPER__ = 'STZ Soft Vicky P'

from CustomSelenium import customSelenium
import pandas as pd
import requests 
import time
import os 


class SolveCaptcha :

    def __init__(self) -> None:
        self.__url = "http://127.0.0.1:8000/captcha"

    def solvecaptcha(self,driver:customSelenium):
        
        image = driver.getXpathValue(xpath_Id="//img[@id='ImageCaptcha']",wait_time=1)
        if  image:               
            imgPath = os.environ.get('Temp')
            imgPath = f"{imgPath}\captcha.png"
            image.screenshot(imgPath)
            res = self.getCaptcha(imgPath)
            os.remove(imgPath)
            if res:
                try:
                    return res.get('predicted')  
                except:
                    pass
        return None

    def getCaptcha(self,imgfile):
        
        #API URL 
        response = None        
        with open(imgfile, "rb") as image_file:
            files = {'file': (imgfile, image_file, 'image/png')}    

            try:
                response =  requests.post(self.__url,files=files)
            except requests.exceptions.ConnectionError as ex:
                pass           
        if response and response.status_code == 200:
            return response.json() 

class TextBox(customSelenium):

    def __init__(self,driver) -> None:
        self.__driver = driver
        self.__textBox = None
        
    def clear(self,xpath):
        textbox = self.__driver.getXpathValue(xpath,wait_time=5)
        textbox.clear()
        self.__textBox = textbox

    def inputText(self,value):        
        self.__textBox.send_keys(value)
       
class IpIndiaV2(customSelenium) :

    def __init__(self) -> None:
        self.__captcha = SolveCaptcha()
        self.__skip_list = list() 
        super().__init__()

    def initialize(self):
        frame = self.getXpathValue("//frame[@name='eregoptions']",wait_time=10)

        self.driver.switch_to.frame(frame)
        self.click(xpath="//a[@id='btnviewdetails']")

        self.driver.switch_to.default_content()
        frame = self.getXpathValue(xpath_Id="//frame[@name='showframe']",wait_time=10)
        
        self.driver.switch_to.frame(frame)
        self.click(xpath="//input[@id='rdb_0']")

    
    def reloadPage(self,tmNo=None):
        self.driver.get(self.driver.current_url)
        self.randomSleep(2,4)
        self.initialize() 

        if tmNo:
            self.__skip_list.append(tmNo)


    def scrape(self,xl_data:pd.DataFrame):        

        self.initialize()        
        textbox = TextBox(driver=self)

        print('\n')

        for tm_no in xl_data: 
            
            if pd.isna(tm_no):
                continue

            tm_no = int(tm_no)        
            data = dict()
            reload_count = 1


            print(f"Currently Extracting TM No '{tm_no}'",end='\r')          

            while True:

                #Tm No Textbox
                textbox.clear(xpath="//input[@name='applNumber']")
                textbox.inputText(value=tm_no)

                # Captcha Textbox
                textbox.clear(xpath="//input[@name='captcha1']")

                #Retrieve API Captcha 
                captcha = self.__captcha.solvecaptcha(driver=self)

                if not captcha:
                    if reload_count == 3:
                        self.reloadPage(tm_no)
                        reload_count = 1
                        break

                    self.reloadPage()
                    reload_count += 1 
                    continue

                textbox.inputText(value=captcha)
                self.click("//input[@name='btnView']")
                table = self.getXpathValue(xpath_Id="//table[@id='SearchWMDatagrid']",wait_time=3)

                if not table:
                    if reload_count == 3:
                        print("Skipped List :" , tm_no)
                        self.reloadPage(tm_no)
                        reload_count = 1  
                        break

                    self.reloadPage()
                    reload_count+= 1
                    continue



                if not self.click(xpath="//table[@id='SearchWMDatagrid']/tbody/tr[2]/td[1]/a",wait_time=5):
                    if reload_count == 3:
                        print("Skipped List :" , tm_no)
                        self.reloadPage(tm_no)
                        reload_count = 1
                        break

                    self.reloadPage()
                    reload_count+= 1

                    continue


                soup = self.getPageSource()
                date = soup.select_one("#lblappdetail > table:nth-of-type(2) > tbody > tr:nth-of-type(1) > td:nth-of-type(1) > b")
                status  = soup.select_one("#lblappdetail > table:nth-of-type(2) > tbody > tr:nth-of-type(2) > td:nth-of-type(1) > font:last-of-type > b")            
                tbody = soup.find('td',string="TM Application No.")
                

                if not tbody:
                    if reload_count == 3:
                        print("Skipped List :" , tm_no)
                        self.reloadPage(tm_no)
                        reload_count = 1
                        break

                    self.reloadPage()
                    reload_count+= 1
                    continue                    
                    
                tbody = tbody.parent.parent
                newdata  = tbody.find_all("td")                                   
                if not newdata:
                    if reload_count == 3:
                        print("Skipped List :" , tm_no)
                        self.reloadPage(tm_no)
                        reload_count = 1  
                        break

                    self.reloadPage()
                    reload_count+= 1
                    continue     

                data.update({
                    "As on Date" : date.text if date else '--',
                    'Status' :status.text if status else '--',
                })

                i = 0
                newdata.pop()   if not len(newdata)  % 2 == 0 else newdata             
                try:
                    while i < len(newdata) :
                        data.update({
                            newdata[i].text if newdata[i] else '' : newdata[i+1].text if newdata[i+1] else '--'
                        })
                        i+= 2
                except:
                    print("Skipped List :" , tm_no)
                    self.reloadPage(tm_no)

                self.save(**data,name=self.file)

                # re-freshing  rather than clicking exit . 
                self.driver.get(self.driver.current_url)
                break

            self.initialize() 

        return self.__skip_list if self.__skip_list else None

    def setFiles(self, fileName : str ):
        self.file = f"{fileName}"



if __name__ == '__main__':
    url = "https://tmrsearch.ipindia.gov.in/eregister/eregister.aspx"
    ip = IpIndiaV2()

    print(f"\n{__VERSION__ } ")    
    ip.randomSleep(1,1)
    print(f"Developed By {__DEVELOPER__ } ")
    ip.randomSleep(1,1)    

    file_name = "wohaa"

    # file_name = input("\nFile Name To Save ? :")
    
    if not file_name :
        print("\t--> Default File Name is Passed , 'IP_India_V2.xlsx'.")
    else:
        print(f"\t --> File will be saved as {file_name}.xlsx")

    
    ip.randomSleep(1,1)    
    while True:
        print("\nPlease pass the 'excel' file containing TM Numbers without '.xlsx' extension")
        # fileXL = "demo"
        fileXL = input("\t--> ") 
        if not fileXL :
            print("\t--> File is mandatory....!\n")
            continue

        tm_number_file = ip.readFile(fileXL+".xlsx")        
        if tm_number_file.empty:
            print("\t--> File not found", fileXL+".xlsx")
            continue
                  
        if not "Tm numbers" in  tm_number_file:
            print("\t--> Invalid header name , Header should be 'Tm numbers'.")
            ip.stop_execute()

        break   

    skip_count = 0
    saved_data = ip.readFile(f"{file_name}.xlsx")


    if not saved_data.empty:
        last_value = saved_data.at[saved_data.index[-1],'TM Application No.']
        skip_count = tm_number_file.index[tm_number_file['Tm numbers'] == last_value].to_list()[0]
        skip_count += 1
        print("\nExtraction Resume....")

    tm_number_file = tm_number_file['Tm numbers'][skip_count::]
    ip.setFiles(file_name)
    ip.intializeDriver()

    try:
        ip.driver.get(url=url)
    except:
        print("Soemthing Wrong , The URL did not load....")
        print(f"\nDeveloped By {__DEVELOPER__ } ")
        print(f"{__DEVELOPER__}")

        ip.stop_execute()


    start_time = time.time()
    skip_list = ip.scrape(tm_number_file)
    ip.closeDriver()    
    end_time = time.time()
    total_seconds = end_time - start_time
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    print("Extraction Completed....")

    if skip_list:
        print("TM Number Skip list ",skip_list)
    
    print(f"\nTotal Time took for Extraction: {int(hours)} hrs {int(minutes)} min {int(seconds)} sec")
    print(f"\nDeveloped By {__DEVELOPER__ } ")
    print('\n\n Press Any Key to Exit')
    input()
