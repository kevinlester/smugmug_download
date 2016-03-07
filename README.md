# smugmug_download
##Description:
Downloads all the files stored in your SmugMug account to your local computer.  Uses multiple queues for downloads to keep everything efficient and handles all the complexities of things like recursive traversing of your folder structure, requesting download URLs, and paging through all the files.

When this script completes, all your smugmug files will be local to your drive, organized into subfolders that mirror the organization of your SmugMug account.  All the images for each album will be found in one or more zip files. 

In order for the script to run, you need to do a few steps first so that the script can have access to your account:  
1. Request an access token for your application.  Go to the following URL to request an application api access key.
https://api.smugmug.com/api/developer/apply  
2. Get the API key and the secret key generated for you, and copy them down.  
3. Clone the smugmug Oauth repo locally:  
   `git clone https://gist.github.com/10046914.git`  
   `cd 10046914`  
4. Copy the example.json to config.json:  
   `cp example.json config.json`  
5. Edit the config.json, and replace the api key and secret key placeholders with the proper values.  
6. Make sure you are using python 3.  If using anaconda (Highly recommended) ensure that you have the python 3 env activated.  
   run the following command, and follow the instructions to get the access token and the access token secret.  
   `run-console.sh`  
   After running the command successfully, you will get an access token, and an access token secret. Copy those down.  
7. Change back to the directory for this repo, and edit the config.json.  You need to enter the following values:  
   `"app_key":           The application api key that was received from Step 2`  
   `"app_key_secret":    The application secret that was received from Step 2`  
   `"access_key":        The OAUTH access key received from Step 6.`  
   `"access_key_secret": The OAUTH access secret key received from Step 6.`  
   `"output_dir":        The directory to which the downloaded albums should be stored.`  
   `"smugmug_user":      The name of the smugmug user for your account.  Easily visible as the first part of your smugmug url.  Example http://<smugmug_user>.smugmug.com`  

   An example config.json is below (don't bother trying this one, it won't work ;):  
   `{`
   `"app_key":           "fUC6J83jfDcZgqUyacHQrL0p8sosiL62",`  
   `"app_key_secret":    "4b043ca632a6e9978ec95372fsf78fs6",`  
   `"access_key":        "3fb43633998b37666157d12345678900",`  
   `"access_key_secret": "eda4a222cf3941a7edaedba63e0df869876772f439afd72f5123456789098e64",`  
   `"output_dir":        "/Users/Kevin/Pictures/smugmug",`  
   `"smugmug_user":      "kevinlester"`  
   `}`

8). Run the downloader python script.  Assuming all the settings are correct, your output directory should eventually be contain the same folder structure as on Smugmug, along with the albums.  The images in the album will be zipped up.  
The script may take a while to run, because it has to go through multiple steps in order to get the images.  Specifically, it needs to traverse the folder structure of the albums, request a download URL for each album, wait for the download URLs to be generated, then download the images.  Depending on how complex your folder structure is, and how many photos/videos you have, it may take a while for the script to complete.

Good Luck!


