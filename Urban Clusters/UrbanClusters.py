'''
UrbanClusters.py
Developed in June 2019 by Jiachen Wei
DATA 599 Capstone Project in collaboaration with Rui Li and Debangsha Sarkar
The University of British Columbia

Supervisors: Milenko Fadic, Paolo Veneri, Alessandro Alasia, Joseph Kuchar, Bruno St-Aubin
Course instructor: Scott Fazackerley

-----------------------------
Input data: a .tif raster file with population values

The program performs the following tasks:
	1. Identify raster cells with population >=300
	2. Group contiguous rasters cells identified in step 1 and create a polygon for each group
	3. Select groups with population sum >= 5000 and export these polygons in a new shapefile
	4. Extract input raster cells within the exported shapefile
	5. Smooth the raster using the majority rule
	6. Convert the smoothed raster to shapefile

Output data: a shapefile 

-----------------------------
The program must be executed in "QGIS Desktop with GRASS" Python Console.
0. Install QGIS
1. Open QGIS Desktop with GRASS 
	The code was developed in QGIS Desktop 3.6.2 with GRASS 7.6.1 in Windows 10
2. Open Python Console in QGIS
	Click on "Show Editor" and then "Open Script"
	Open UrbanClusters.py in Python Console
	Set up the following parameters (input and output paths)
	Click "Run Script"
'''

from osgeo import gdal,osr
import struct
import numpy as np

###########################################
#Set up the following parameters 
#before running the code
###########################################

#Note the the use of slashes might be different in other operating systems

#Input data
rasterFile = "C:\\Users\\Jiachen\\OneDrive\\MDS Labs Submitted\\data599\\UrbanClusters\\ghs_2015_1km.tif"

#Specify a folder (preferably an empty folder) to store temporary output files.
#All files in this folder can be used for validation and deleted after executing the program.
#It's recommended but not required to empty this folder before running the code
TEMP = "C:\\Users\\Jiachen\\OneDrive\\MDS Labs Submitted\\data599\\UrbanClusters\\TempOutputs"
#Specify a folder to store final output files.
#It's recommended but not required to empty this folder before running the code
FO = "C:\\Users\\Jiachen\\OneDrive\\MDS Labs Submitted\\data599\\UrbanClusters\\FinalOutputs"

###########################################
#Load input data and validate
###########################################
#Remove all current layers
QgsProject.instance().clear()

rlayer = iface.addRasterLayer(rasterFile,"Input Data","gdal")
if rlayer.isValid():
    print("This is a valid raster layer")
else:
    print("The input raster layer is invalid")
crs = '['+ rlayer.crs().authid() +']'

#############################################
#Identify raster cells with population >=300
#############################################

#Ratster value <300 will be reclassified to 0, and >=300 reclassified to 1
processing.run("gdal:rastercalculator", 
    {'INPUT_A':rasterFile,'BAND_A':1,
    'INPUT_B':None,'BAND_B':-1,'INPUT_C':None,'BAND_C':-1,'INPUT_D':None,'BAND_D':-1,'INPUT_E':None,'BAND_E':-1,'INPUT_F':None,'BAND_F':-1,
    'FORMULA':'(A >= 300) * 1','NO_DATA':None,'RTYPE':5,'OPTIONS':'',
    'OUTPUT':TEMP+'\\Reclass300.tif'})

#Set raster cells with value 0 to nodata
processing.run("gdal:translate", 
    {'INPUT':TEMP+'\\Reclass300.tif',
    'TARGET_CRS':QgsCoordinateReferenceSystem(crs),'NODATA':0,'COPY_SUBDATASETS':False,'OPTIONS':'','DATA_TYPE':0,
    'OUTPUT':TEMP+'\\ReclassND.tif'})

#############################################
#Vectorize contiguous raster cells >= 300
#############################################

#Group contiguous raster cells with value 1
processing.run("grass7:r.clump",
    {'input':TEMP+'\\ReclassND.tif',
    'title':'Group300','-d':False,
    'output':TEMP+'\\Group300.tif',
    'GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})

#Convert each group of raster cells to a polygon
processing.run("gdal:polygonize", 
    {'INPUT':TEMP+'\\Group300.tif',
    'BAND':1,'FIELD':'ID','EIGHT_CONNECTEDNESS':False,
    'OUTPUT':TEMP+'\\Group300.shp'})

#############################################
#Select population sum >= 5000
#############################################

#Multiply input raster values with Reclass300 (0 or 1)
#Raster cells with values <300 will be set to value 0
processing.run("gdal:rastercalculator", 
    {'INPUT_A':rasterFile,'BAND_A':1,
    'INPUT_B':TEMP+'\\Reclass300.tif','BAND_B':1,
    'INPUT_C':None,'BAND_C':-1,'INPUT_D':None,'BAND_D':-1,'INPUT_E':None,'BAND_E':-1,'INPUT_F':None,'BAND_F':-1,
    'FORMULA':'A*B','NO_DATA':None,'RTYPE':5,'OPTIONS':'',
    'OUTPUT':TEMP+'\\InputX01.tif'})

#Set raster cells with value 0 to nodata
processing.run("gdal:translate", 
    {'INPUT':TEMP+'\\InputX01.tif',
    'TARGET_CRS':QgsCoordinateReferenceSystem(crs),'NODATA':0,'COPY_SUBDATASETS':False,'OPTIONS':'','DATA_TYPE':0,
    'OUTPUT':TEMP+'\\InputND.tif'})

#Add a new colum pop_sum (population sum) to the shapefile
processing.run("qgis:zonalstatistics", 
    {'INPUT_RASTER':TEMP+'\\InputND.tif','RASTER_BAND':1,
    'INPUT_VECTOR':TEMP+'\\Group300.shp',
    'COLUMN_PREFIX':'pop_','STATS':[1]})

#Select pop_sum >= 5000 in Group300.shp and save as a new shapefile
TempLayer= iface.addVectorLayer(TEMP+'\\Group300.shp','TempLayer','ogr')
TempLayer.selectByExpression('"pop_sum" >= 5000', QgsVectorLayer.SetSelection)
QgsVectorFileWriter.writeAsVectorFormat(
    TempLayer, TEMP+'\\Group5000.shp', 'System', 
    QgsCoordinateReferenceSystem(crs), 'ESRI Shapefile', onlySelected=True)
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)

#############################################
#Extract raster cells within the polygons
#############################################

#Fix geometries of the input data files
processing.run("native:fixgeometries", 
    {'INPUT':TEMP+'\\Group5000.shp','OUTPUT': TEMP+'\\Group5000_fixed.shp'})

#Clip raster by vector mask
processing.run("gdal:cliprasterbymasklayer", 
    {'INPUT':TEMP+'\\Group300.tif',
    'MASK':TEMP+'\\Group5000_fixed.shp',
    'SOURCE_CRS':QgsCoordinateReferenceSystem(crs),'TARGET_CRS':QgsCoordinateReferenceSystem(crs),'NODATA':None,'ALPHA_BAND':False,'CROP_TO_CUTLINE':False,
    'KEEP_RESOLUTION':True,'SET_RESOLUTION':False,'X_RESOLUTION':None,'Y_RESOLUTION':None,'MULTITHREADING':False,'OPTIONS':'','DATA_TYPE':0,
    'OUTPUT':TEMP+'\\Group300Clipped.tif'})
    
#############################################
#Smooth the raster using the majority rule
#############################################

#Read raster file as numpy.ndarray
path= TEMP+'\\Group300Clipped.tif'
dataset = gdal.Open(path)
band = dataset.GetRasterBand(1)

data = band.ReadAsArray()  #numpy.ndarray
height = band.YSize #total number of rows
width = band.XSize  #total number of columns
nd = data.max()  #the array value representing nodata in the raster
#data[row] is a row containing band.XSize elements
#data[row,col] is an element


#Apply majority filter to each nodata cell
    #A cell will change its value if at least 5 of its 8 sourrounding cells belong to the same cluster (having the same ID)
#Iterate over each raster cell excluding the four edges
for i in range (1,height-1):
    for j in range (1,width-1):
        if data[i,j] == nd:
			#Create a list to stroe the values of 8 neighboring cells
            neighbors = [
                data[i-1,j-1],data[i-1,j],data[i-1,j+1],
                data[i,j-1], data[i,j+1],
                data[i+1,j-1],data[i+1,j], data[i+1,j+1]]
			#If 5/8 neighbors have the same value, the current raster cell will be assigned that value
            for ele in set(neighbors):
                if neighbors.count(ele) >=5:
                    data[i,j] = ele

#Write array to raster file
geotransform = dataset.GetGeoTransform()
wkt = dataset.GetProjection()
driver = gdal.GetDriverByName("GTiff")

dst_ds = driver.Create(
    TEMP+"\\HighDensityClusters.tif",
    band.XSize,
    band.YSize,
    1,
    band.DataType)
#writting output raster
dst_ds.GetRasterBand(1).WriteArray(data)
#setting nodata value
dst_ds.GetRasterBand(1).SetNoDataValue(float(nd))
#setting extension of output raster
    #top left x, w-e pixel resolution, rotation, top left y, rotation, n-s pixel resolution
dst_ds.SetGeoTransform(geotransform)
#setting spatial reference of output raster
srs = osr.SpatialReference()
srs.ImportFromWkt(wkt)
dst_ds.SetProjection( srs.ExportToWkt() )

#Repeat writing array to .tif to prevent reading and projecting errors
geotransform = dataset.GetGeoTransform()
wkt = dataset.GetProjection()
driver = gdal.GetDriverByName("GTiff")
dst_ds = driver.Create(
    TEMP+"\\HighDensityClusters.tif",
    band.XSize,
    band.YSize,
    1,
    band.DataType)
dst_ds.GetRasterBand(1).WriteArray(data)
dst_ds.GetRasterBand(1).SetNoDataValue(float(nd))
dst_ds.SetGeoTransform(geotransform)
srs = osr.SpatialReference()
srs.ImportFromWkt(wkt)
dst_ds.SetProjection( srs.ExportToWkt() )

#############################################
#Convert raster to shapefile
#############################################

processing.run("gdal:polygonize", 
    {'INPUT':TEMP+"\\HighDensityClusters.tif",
    'BAND':1,'FIELD':'ID','EIGHT_CONNECTEDNESS':False,
    'OUTPUT':FO+'\\HighDensityClusters.shp'})

#############################################
#Load the final output
#############################################

#The groups with raster cell >= 300 and pop_sum >= 5000
HDC = iface.addVectorLayer(FO+'\\HighDensityClusters.shp', 'HDC','ogr')

print("All completed.")
print("Each polygon in the HDC layer represents a group of raster cells with each cell >= 300 and group sum >= 5000")