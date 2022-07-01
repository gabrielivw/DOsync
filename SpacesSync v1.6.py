"""
Created by G. Isaacman-VanWertz, April 2021
Used to sync a data repository in a DigitalOcean droplet with a local folder
Can be used for upload and/or download

Uses a config file to define file types and repository name

Known bugs/quirks as of v 1.6:

-fails if there are no files in the droplet.
-binary flag to skip the last file in case it is still being written is flipped, set to 0 if you want to skip the last file
-requires the config file is named DO_config.cfg and is located in C:\DOSync\
-sometimes seems to lose connection or access and must be closed and restarted. Not sure why this is or how to fix.
"""

import boto3
from botocore.client import Config
from pathlib import Path
from os import listdir, mkdir
from os.path import isfile, join, isdir
from datetime import datetime, timedelta
import time

                
class config:
    """
    Class that contains information important from a config file
    """
    def __init__(self):
        self.folder = ""
        self.name = ""
        self.key = ""
        self.secretkey = ""
        self.region = ""
        self.delay = 0
        self.ext = ""
        self.skiplast = 0
        self.upload = 0
        self.download = 0
        

def startsession(config):
    """
    Use config information to initialize a DigitalOceans session
    Return session information
    """
    session = boto3.session.Session()
    url = 'https://' + config.region + '.digitaloceanspaces.com'
    try:
        client = session.client('s3',
                            region_name=config.region,
                            endpoint_url=url,
                            aws_access_key_id=config.key,
                            aws_secret_access_key=config.secretkey)
    except Exception as e:
        print(str(e))
        
    return client

        
        
    
def readconfig(pathstr):
    """
    Imports information from a config file that looks like:
      SyncFolder=C:/Projects/;
      SpacesName=vfl-bvoc-1;
      AccessKey=EXAMPLE012334567;
      SecretAccessKey=EXAMPLE012334567ABCDEFGH;
      Region=sfo3;
      Delay=60;
      Extension=.abc,.def;
      UploadSkipLast=1;
      DoUpload=1;
      DoDownload=1;
      
      Delay is in seconds. Keys come from DigitalOcean. Extension can be a list, but does not have to be. UploadSkipLast,
        DoUpload, and DoDownload are binary flags
    Returns a config class containing information read in
    """
    
    configfile = open(pathstr, "r")
    configstr = ""
    keylist = []
    vallist = []
    while(1):
        configdata = configfile.readline()
        if(not(len(configdata)>0)):
            break
        keystr = configdata.split('=')[0]
        valstr = configdata.split('=')[1]
        valstr = valstr.split(';')[0]
        keylist.append(keystr)
        vallist.append(valstr)
    configfile.close()
    
    data = config
    data.folder=vallist[keylist.index('SyncFolder')]
    data.name=vallist[keylist.index('SpacesName')]
    data.key=vallist[keylist.index('AccessKey')]
    data.secretkey=vallist[keylist.index('SecretAccessKey')]
    data.region=vallist[keylist.index('Region')]
    data.delay= int(vallist[keylist.index('Delay')])
    data.ext = tuple(vallist[keylist.index('Extension')].strip().split(","))
    data.skiplast= int(vallist[keylist.index('UploadSkipLast')])
    data.upload= int(vallist[keylist.index('DoUpload')])
    data.download= int(vallist[keylist.index('DoDownload')])
    
    return data


def getnewfiles(localpath, DOsession, config):
    """
    cross-check local and remote folders
    
    localpath is the path string to the local folder
    DOsession is the session returned by startsession()
    configdata is a config class with all the information
    
    returns two strings:
    newfolderfiles is local files not in Spaces
    newspacesfiles is Spaces files not available locally
    """
    data_folder = Path(config.folder)

    #list all files in spaces bucket
    spacesfiles=[]
    
    paginator = DOsession.get_paginator("list_objects_v2")
    
    try:
        for page in paginator.paginate(Bucket=config.name):
            spacesfiles = spacesfiles + [obj['Key'] for obj in page['Contents'] if obj['Key'].endswith(config.ext)]
    
    except Exception as e:
        raise e
    
    #list all files that end in .txt in specified folder
    folderfiles = [f for f in listdir(data_folder) if (isfile(join(data_folder, f)) and join(data_folder, f).endswith(config.ext))]

    #check the modification date of all files in specified folder
    lasttime = 0
    if(len(folderfiles)>1): # if one or fewer files is found, we probably shouldn't worry about uploading anything
         
        # catalog files not on Spaces
        newfolderfiles = [f for f in folderfiles if not(f in spacesfiles)]
        
        #determine and remove the most recently modified file from the list. This one might still be getting written to by the instrument  
        if(not(config.skiplast == 1)):
            for obj in folderfiles:
                file_to_open = data_folder / obj
                mtime = (file_to_open.stat().st_mtime)

                if (mtime>lasttime):
                    lasttime = mtime
                    lastfile = obj

            if(lastfile in newfolderfiles):
                newfolderfiles.remove(lastfile) 
    else:
        newfolderfiles=""
        
    #catalog files not in folder
    newspacesfiles = [f for f in spacesfiles if not(f in folderfiles)]
    
    return newfolderfiles,newspacesfiles



configpath = "C:/DOSync/"
config = readconfig(configpath+"DO_Config.cfg")
client = startsession(config)
delaytime = timedelta(seconds = config.delay)

now=datetime.now()
lastcheck = now-2*delaytime
data_folder = Path(config.folder)

#create log directory if not available
logpath = join(configpath, 'log')
if(not(isdir(Path(logpath)))):
    mkdir(logpath) 

#name log file
logname = logpath+"/log_"
logname+=now.strftime("%Y%m%d%H%M%S")
logname += ".txt"

#initialize log file
logfile = open(logname, "a")
    
output=logname
output+="\n*****\n"
output+= "folder = " + config.folder +"\n"
output+= "delay = " + str(config.delay) + " seconds\n"
output+= "space = " + config.name+"\n"
output+= "extensions = " + str(config.ext)+"\n"
output+="*****\n"
output+= str(datetime.now()) + ": initialized"
print(output, file=logfile)
logfile.close()
print(output)

# loop until program is closed as long as you can find the sync folder
while(isdir(data_folder)):  
    now=datetime.now()

    if((now-lastcheck) > delaytime):
        lastcheck=datetime.now()

        try:
            newfolderfiles,newspacesfiles = getnewfiles(config.folder,client,config)
        except Exception as e:
            output=str(e)
            logfile = open(logname, "a")
            print(output, file=logfile)
            logfile.close()
            print(output)

        #upload new folder files
        if(len(newfolderfiles)>0 and config.upload==1):
            for obj in newfolderfiles:
                file_to_open = data_folder / obj
                output = str(datetime.now()) + ": Uploaded " + str(file_to_open)
                
                try:
                    client.put_object(Bucket=config.name,
                                  Key=obj,
                                  Body=open(file_to_open, 'rb'),
                                  ACL='private',
                                )
                except Exception as e:
                    output += "   FAILED"
                    print(str(e))
                

                logfile = open(logname, "a")
                print(output, file=logfile)
                logfile.close()
                print(output)
                
        #download new spaces files
        if(len(newspacesfiles)>0 and config.download==1):
            for obj in newspacesfiles:
                output = str(datetime.now()) + ": Downloaded "+ join(data_folder, obj)
                
                try:
                    client.download_file(config.name,
                                 obj,
                                 join(data_folder, obj))
                except Exception as e:
                    output += "   FAILED"
                    print(str(e))

                logfile = open(logname, "a")     
                print(output, file=logfile)
                logfile.close()
                print(output)
                
    
    time.sleep(1) 

