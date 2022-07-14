import os
from osgeo import gdal, ogr,osr
import sys
import json
import geojson as gj
import numpy as np
import argparse
import csv


gdal.UseExceptions()

GDAL_MEMORY_DRIVER = gdal.GetDriverByName('MEM')
OGR_MEMORY_DRIVER = ogr.GetDriverByName('Memory')


def cut_by_geojson(input_file, output_file, shape_geojson='limassol_box.geojson'):

    # Get coords for bounding box
    with open(shape_geojson) as data_file: 
        geoms= json.load(data_file)
        x,y =  zip(*gj.utils.coords(geoms))
        wkt_geom = ogr.CreateGeometryFromJson(str(geoms['features'][0]['geometry']))
    #shape_geojson = geoms
    min_x, max_x, min_y, max_y = min(x), max(x), min(y), max(y)

    # Open original data as read only
    dataset = gdal.Open(input_file, gdal.GA_ReadOnly)
    
    bands = dataset.RasterCount
    print(bands)
    # Getting georeference info
    transform = dataset.GetGeoTransform()
    print(transform)
    projection = dataset.GetProjection()
    print(projection)
    #transform = (-60.00208333335, 0.0041666667, 0.0, 75.00208333335, 0.0, -0.0041666667)
    #transform = (59.99791666665, 0.0041666667, 0.0, 75.00208333335, 0.0, -0.0041666667)
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = -transform[5]

    # Getting spatial reference of input raster
    srs = osr.SpatialReference()
    srs.ImportFromWkt(projection)

    # WGS84 projection reference
    OSR_WGS84_REF = osr.SpatialReference()
    OSR_WGS84_REF.ImportFromEPSG(4326)

    # OSR transformation
    wgs84_to_image_trasformation = osr.CoordinateTransformation(OSR_WGS84_REF,
                                                                srs)
    XYmin = wgs84_to_image_trasformation.TransformPoint(min_x, max_y)
    XYmax = wgs84_to_image_trasformation.TransformPoint(max_x, min_y)

    # Computing Point1(i1,j1), Point2(i2,j2)
    i1 = int((XYmin[0] - xOrigin) / pixelWidth)
    j1 = int((yOrigin - XYmin[1]) / pixelHeight)
    i2 = int((XYmax[0] - xOrigin) / pixelWidth)
    j2 = int((yOrigin - XYmax[1]) / pixelHeight)
    new_cols = i2 - i1 + 1
    new_rows = j2 - j1 + 1

    # New upper-left X,Y values
    new_x = xOrigin + i1 * pixelWidth
    new_y = yOrigin - j1 * pixelHeight
    new_transform = (new_x, transform[1], transform[2], new_y, transform[4],
                     transform[5])

    #wkt_geom = ogr.CreateGeometryFromJson(str(shape_geojson))
    wkt_geom.Transform(wgs84_to_image_trasformation)

    target_ds = GDAL_MEMORY_DRIVER.Create('', new_cols, new_rows, 1,
                                          gdal.GDT_Byte)
    target_ds.SetGeoTransform(new_transform)
    target_ds.SetProjection(projection)

    # Create a memory layer to rasterize from.
    ogr_dataset = OGR_MEMORY_DRIVER.CreateDataSource('shapemask')
    ogr_layer = ogr_dataset.CreateLayer('shapemask', srs=srs)
    ogr_feature = ogr.Feature(ogr_layer.GetLayerDefn())
    ogr_feature.SetGeometryDirectly(ogr.Geometry(wkt=wkt_geom.ExportToWkt()))
    ogr_layer.CreateFeature(ogr_feature)

    gdal.RasterizeLayer(target_ds, [1], ogr_layer, burn_values=[1],
                        options=["ALL_TOUCHED=TRUE"])

    # Create output file
    driver = gdal.GetDriverByName('GTiff')
    outds = driver.Create(output_file, new_cols, new_rows, bands,
                          gdal.GDT_Float32)

    # Read in bands and store all the data in bandList
    mask_array = target_ds.GetRasterBand(1).ReadAsArray()
    band_list = []

    for i in range(bands):
        band_list.append(dataset.GetRasterBand(i + 1).ReadAsArray(i1, j1,
                         new_cols, new_rows))

    for j in range(bands):
        data = np.where(mask_array == 1, band_list[j], mask_array)
        outds.GetRasterBand(j + 1).SetNoDataValue(0)
        outds.GetRasterBand(j + 1).WriteArray(data)

    outds.SetProjection(projection)
    outds.SetGeoTransform(new_transform)

    target_ds = None
    dataset = None
    outds = None
    ogr_dataset = None


def health_check(image):
    dataset = gdal.Open(image,gdal.GA_ReadOnly)
    for x in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(x)
        array = band.ReadAsArray()
        #print(np.mean(array, axis=None))
        zeros = np.count_nonzero(array==0.0)
        total = np.count_nonzero(array)
        if zeros > 0.25*total:
            return False
        else:
            return True
    

def processImage(image):
    dataset = gdal.Open(image,gdal.GA_ReadOnly)
    for x in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(x)
        array = band.ReadAsArray()
        #print(np.mean(array, axis=None))
        #print(np.count_nonzero(array>0.0))
        #(array)
        array[array < 0.3] = 0
        print(np.mean(array))
        #print(array)
        #print()
        #print(array.shape,type(array))
    return np.mean(array)

def extractMonthYear(image):
    year = image[10:14]
    month = image[14:16]
    return month,year
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--dir', metavar='dir', type=str,
                        help='Directory with the extracted .tif files')

    parser.add_argument('--geojson', metavar='geojson', type=str,
                        help='geojson file to crop the area')
    
    parser.add_argument('--saveDir',metavar='saveDir',default="cropped",type=str,
                        help='directory to save the cropped .tif files')

    parser.add_argument('--process',metavar='process', choices=["False","True"],
                        help='Set to True to extract a .csv file, you also need to specify --processDir')

    parser.add_argument('--processDir',metavar='processDir',default='cropped',
                        help="Specify Directory with the saved cropped .tif images to process")

    parser.add_argument('--outcsv',metavar='outcsv',default="result.csv",
                        help="Specify csv filename to store the results of processing (Only if process=True)")



    args = parser.parse_args()
    
    if args.process=="True":
        rowlist=[]
        files = os.listdir(args.processDir)
        for f in files:
            month,year = extractMonthYear(f)
            mean = processImage(os.path.join(args.processDir,f))
            if mean==0:
                continue
            rowlist.append([month+"-"+year,mean])
            print(month,year,mean)
        outfile = args.outcsv
        if ".csv" not in outfile:
            outfile=outfile+".csv"
        with open(outfile, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rowlist)
        #with open("")
    else:
        with open("corruptedtifs.txt","w") as f:
            f.close()

        try:
            filesToParse = os.listdir(args.dir)
            print(len(filesToParse))
        except:
            sys.exit("Problem with input directory")
        
        if not os.path.isdir(args.saveDir):
            os.mkdir(args.saveDir)
        
        
        for i,f in enumerate(filesToParse):
            print(f)
            outfile =os.path.join(args.saveDir,f.split(".")[0]+"_cropped"+".tif")
            inputFile = os.path.join(args.dir,f)
            #cut_by_geojson(inputFile,outfile,shape_geojson=args.geojson)
            try:
                if "avg_rade9h" in f:
                    cut_by_geojson(inputFile,outfile,shape_geojson=args.geojson)
            except:
                print("Got In here")
                with open("corruptedtifs.txt","a+"):
                    f.write(str(f))
                    f.write("\n")



        # Healthcheck cropped Images
        healthcheck=True
        cropped_imgs = os.listdir(args.saveDir)
        for cropped_img in cropped_imgs:
            path = os.path.join(args.saveDir,cropped_img)
            if health_check(path) == False and healthcheck==True:
                with open('corruptedtifs.txt','a+') as f:
                    f.write(str(cropped_img))
                    f.write("\n")
            #print(cropped_img)
    

