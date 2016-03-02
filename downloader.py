'''
Created on Jul 4, 2015

@author: Kevin Lester
'''
import json
import time
from time import sleep
import os
import requests
from requests_oauthlib import OAuth1
from multiprocessing import Pool, Manager

current_milli_time = lambda: int(round(time.time() * 1000))


def dl_process_init(dl_queue, sleep_queue, master_albums_list, api_key_params, oauth_data):
    while 1:
        downloadRequest = dl_queue.get()
        initiateDownload(downloadRequest['node'], downloadRequest['path'], sleep_queue, master_albums_list, api_key_params, oauth_data)

def sleep_process_init(dl_queue, sleep_queue, api_key_params, oauth_data):
    while 1:
        sleepRequest = sleep_queue.get()
        queueForSleeping(sleepRequest['node'], sleepRequest['path'], sleepRequest['queueTimeMillis'], dl_queue)


def queueForSleeping(node, path, queueTimeMillis, dl_queue):
    currentMillis = current_milli_time()
    sleepTime = 5 - (currentMillis - queueTimeMillis)/1000
    if sleepTime > 0 :
        sleep(sleepTime)
    dl_queue.put ({'node' : node, 'path' : path})


def downloadAlbum(uri, fileName, oauth_data):
    response = requests.get(uri, auth=(oauth_data), timeout=20.0)
    if os.path.exists(fileName):
        if os.path.getsize(fileName) == int(response.headers['content-length']):
            # we already have it local
            return
    if response.ok:
        with open(fileName, 'wb') as fd:
            for chunk in response.iter_content(1024):
                fd.write(chunk)
        

def requestNewDownloadUrl(downloadUrl, node, path, master_albums_list, oauth_data):
    response = requests.post(downloadUrl, auth=(oauth_data))
    if response.status_code == 202:
        sleep_queue.put({'node' : node, 'path' : path, 'queueTimeMillis' :current_milli_time()})
    else:
        print ('Request to queue failed for (uri, path): (%s, %s) ' % (downloadUrl, path))
        master_albums_list.remove(path)


def initiateDownload(node, path, sleep_queue, master_albums_list, api_key_params, oauth_data):
    downloadUrl = 'http://api.smugmug.com%s!download' % node['Uris']['Album']['Uri']
    response = requests.get(downloadUrl, params=api_key_params, auth=(oauth_data))
    if not response.status_code == 200:
        print ('Error getting node for dir: ' + path)
        return
    responseJson = response.json()['Response']
    if 'Download' in responseJson:
        for downloadJson in responseJson['Download']:
            # if the Download status is 'Removed', we need to repost to it to trigger a new download
            if downloadJson['Status'] == 'Removed':
                requestNewDownloadUrl(downloadUrl, node, path, master_albums_list, oauth_data)
                return
            if downloadJson['Status'] != 'Complete':
                sleep_queue.put({'node' : node, 'path' : path, 'queueTimeMillis' :current_milli_time()})
                return
        #if we got here, then all downloads are ready to go!
        for downloadJson in responseJson['Download']:
            uri = downloadJson['WebUri']
            fileName = downloadJson['FileName']
            downloadAlbum(uri, path + '/' + fileName, oauth_data)
        master_albums_list.remove(path)
    else:
        # We don't have a download URL yet.  request one.
        requestNewDownloadUrl(downloadUrl, node, path, master_albums_list, oauth_data)
    
    
def getNodeURI(userAcct, api_key_params, oauth_data):
    #Get the top level folders
    response = requests.get('https://api.smugmug.com/api/v2/folder/user/%s' % userAcct, params=api_key_params, auth=oauth_data)
    if response.status_code != 200:
        print ('ERROR')
        exit -1
    responseJson = response.json()
    nodeURI = responseJson['Response']['Folder']['Uris']['Node']['Uri']
    #print (nodeURI)
    return nodeURI


def processFolder(rootNodeURI, rootDir, api_key_params, oauth_data):
    rootNodeURI = 'http://api.smugmug.com%s' % rootNodeURI
    if not '!children' in rootNodeURI:
        rootNodeURI += '!children'
    #print ('url = ' + rootNodeURI)
    response = requests.get(rootNodeURI, params=api_key_params, auth=oauth_data)
    if response.status_code != 200:
        print ('ERROR')
        exit
    responseJson = response.json()
    #print (responseJson)
    for node in responseJson['Response']['Node']:
        name = node['Name']
        path = '%s/%s' % (rootDir, name)
        #print (path)
        os.makedirs(path,exist_ok=True)
        if node['Type'] == 'Folder':
            processFolder(node['Uri'], path, api_key_params, oauth_data)
        elif node['Type'] == 'Album':
            #Queue for download
            master_albums_list.append(path)
            dl_queue.put({'node' : node, 'path' : path})
    pages = responseJson['Response']['Pages']
    if pages and 'NextPage' in pages:
        processFolder(pages['NextPage'], rootDir, api_key_params, oauth_data)


def loadConfigData():
    try:
        #If the config.json is not in the current directory, then change this to the absolute path
        with open('config.json', 'r') as fh:
            config = json.load(fh) 
            api_key_params = {'APIKey' : config['app_key'], '_accept' : 'application/json'}
            oauth_data = OAuth1(config['app_key'], 
                                  config['app_key_secret'],
                                  config['access_key'], 
                                  config['access_key_secret'])
            return config, api_key_params, oauth_data
    except IOError as e:
        print('Could not open config.json. Please ensure it exists')
        sys.exit(1)


manager = Manager()
dl_queue = manager.Queue()
sleep_queue = manager.Queue()
master_albums_list = manager.list()

if __name__ == '__main__':
    config, api_key_params, oauth_data = loadConfigData()
    # Initialize the pools
    dl_pool = Pool(processes=4, initializer=dl_process_init, initargs=(dl_queue, sleep_queue, master_albums_list, api_key_params, oauth_data))
    sleep_pool = Pool(processes=1, initializer=sleep_process_init, initargs=(dl_queue, sleep_queue, api_key_params, oauth_data))
    # Get the root node
    nodeURI = getNodeURI(config['smugmug_user'], api_key_params, oauth_data)
    # Process the folder, which will subsequently process all subfolders.
    processFolder(nodeURI, config['output_dir'], api_key_params, oauth_data)
    # Chill out until all the folders have been processed.
    while master_albums_list:
        #wait for all the files to be processed.
        sleep(10)
    print ('Done!')

