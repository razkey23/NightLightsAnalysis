# Night Light Analysis
This repository contains the code/scripts needed to download data from VIIRS-DNB Night-lights monthly composites (Tile 2). The analysis will be carried out only for regions inside EUROPE. (For other regions the code can be easily modified to download another tile from the datasource)

## Workflow Overview
Assuming that we have an Area of Interest (specified in a geojson) we want to find the trend of night time activity during a specified time interval. To do so, we do the following :
1. Retrieve data (zipped format) from VIIRS-DNB
2. Extract the given data in a specified folder
3. Crop the tile based on a given Area of Interest
4. Process the cropped image and derive mean of pixels (=mean radiance nW/cm2/sr) 
5. Export them into a .csv
6. **(Optional)** For a couple of months the vcmcfg images are corrupted therefore there is an option to determine those images and download vcmslcfg instead. And re-run the analysis

## Setup
Preferably you can set up in a conda environment but it is certainly not necessary. Important packages that need to be installed are:
```
gdal (use conda-forge gdal in a conda environment)
numpy
clint-ui
beatifulsoup-bs4
```

## Sample use-case scenario
Let's say that I want to find the nightlights activity for geojson/crete.geojson (Large area is sea in my geojson, that should be avoided) from January 2017 until December 2021.

### Step 1 : Credentials Config
Create a credentials.json file with user information that is registered [here](https://eogauth.mines.edu/auth/realms/master/protocol/openid-connect/auth?response_type=code&scope=email%20openid&client_id=eogdata_oidc&state=VaWVV-zqgTp7CuL5heI6lnRSJzo&redirect_uri=https%3A%2F%2Feogdata.mines.edu%2Feog%2Foauth2callback&nonce=4gZPvWOSxjKvNbCH4M197UjtrfiusZgiyXdzQU4iyYQ).
Example
```json
{
    "username": "username", 
    "password": "password"
}
```

### Step 2 : Download Data
Run the script *data_download.py* in the following manner
```bash
python data_download.py --startdate 012017 --enddate 122021 --saveDir storage
```
This way the download process will begin. The stored .tgz files will be saved in a new directory that is named storage.


**Resume from a saved state**: 
During the download process a new file will be created named *savedproducts.txt* containing all the files that have already been downloaded. If you want to resume from a saved state you can run the following command
```
python data_download.py --startdate 012017 --enddate 122021
--saveDir storage --resume True
```

### Step 3 : Extract files
Now after having downloaded all the files you need to extract them. You can do that by running the following script
```bash
python extractfiles.py --zipdir storage --extractdir extractedFiles
```
This way you will extract all the files stored in *storage* and save them in a new folder named *extractedFiles*. 


**WARNING**: A lot of storage space is needed.

### Step 4 : Process file
The result of extraction are a lot of .tif files that contain information regarding the radiance in the whole tile-2 (Europe region). Now assuming that we have a geojson with our Area of Interest we can run the following command to obtain .csv that looks like results/results_crete.csv

1. Get cropped .tif files based on our AoI
```
python parseImage.py --dir extractFiles --geojson geojsons/crete.geojson --saveDir croppedImages
```

2. Analyze those cropped Images
```
python parseImage.py --process True --processDir croppedImages --outcsv results_crete.csv
```


### Step 5 : Corrupted Images (Optional)
Now because some of the .tif files are corrupted (cropped Image appears 100% black). These images can be found in a .txt files named corruptedtifs.txt that is created during step 4. Now using that file we can download vcmslcfg files in order to *fill* our timeseries with data.

To download those auxiliary images:
```bash
python download_data.py --corrupted True --saveDir corruptedTifs
```

Now extract them
```
python extractFiles.py --zipdir corruptedTifs --extractdir extractFiles
```

Now in your extractFiles folder you have all the data you need to re-run  the analysis and obtain a timeseries without any NaN values

```
python parseImage.py --dir extractFiles --geojson geojsons/crete.geojson --saveDir croppedImages
python parseImage.py --process True --processDir croppedImages --outcsv results_crete.csv
```

 