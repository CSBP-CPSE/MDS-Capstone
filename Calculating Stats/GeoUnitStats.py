'''
GeoUnitStats.py
Developed in May 2019 by Jiachen Wei
DATA 599 Capstone Project in collaboaration with Rui Li and Debangsha Sarkar
The University of British Columbia

Supervisors: Alessandro Alasia, Joseph Kuchar, Bruno St-Aubin, Milenko Fadic, Paolo Veneri
Course instructor: Scott Fazackerley

-----------------------------
Input data: three shapefiles extracted from the data sources
	1. building footprints (BF)
	2. census tracts (CT) of the study area
	3. dissemination blocks (DB) of the same study area

The program performs the following tasks:
	1. Load data and generate 1 km2 grid (GRID) based on the CT extent
	2. Validate and preprocess the input data   
	3. Calculate edge distance between nearest building polygons using NNJoin
	4. Calculate average size (AvgSize) for CT, DB and GRID
	5. Calculate building density (BD) for CT, DB and GRID
	6. Calculate building coverage ratio (BCR) for CT, DB and GRID
	7. Calculate building proximity (ProxMean) for CT, DB and GRID
	8. Calculate building contiguity (ContRatio) for CT, DB and GRID
	9. Load the final outputs into QGIS  
	
Output data: three shapefiles
	1. Building statistics of the input census tracts (CT)
	2. Building statistics of the input dissemination blocks (DB)
	3. Building statistics of the generated 1 km2 grid (GRID) based on the CT extent
-----------------------------

The program must be executed in "QGIS Desktop" Python Console.
0. Install QGIS
1. Open QGIS Desktop with GRASS 
	The code was developed in QGIS Desktop 3.6.2 in Windows 10
2. Install the NNJoin plugin
	Click on Plugins --> Manage and Install Plugins --> search for NNjoin and install
3. Open Python Console in QGIS
	Click on "Show Editor" and then "Open Script"
	Open GeoUnitStats.py in Python Console
	Set up the following parameters (input and output paths)
	Click "Run Script"
'''

import os
from qgis.core import *
import processing
from qgis.utils import plugins

###########################################
#Set up the following parameters 
#before running the code
###########################################

#Note the the use of slashes might be different in other operating systems

#Input data: shapefiles for building footprints (BF), census tracts (CT), and dissemination blocks (DB)
#It is required that the input CT and DB files are of the same extent. For example, the CT and DB of the same city or of the same province.
#Only the extent of CT will be considered in the following steps as the shapefile is smaller.
BF= "C:\\Fred_NB\\Fred_NB Building Footprint\\Fredericton_NewBrunswick.shp"
CT= "C:\\Fred_NB\\Fred_NB Census Tract\\Fredericton_NewBrunswick_census_tract.shp"
DB= "C:\\Fred_NB\\FredDB\\FredDB.shp"

#Specify a folder (preferably an empty folder) to store temporary output files.
#All files in this folder can be used for validation or deleted after executing the program.
#It's recommended but not required to empty this folder before running the code
TEMP = "C:\\Fred_NB\\TempOutputs"
#Specify a folder to store final output files.
#It's recommended but not required to empty this folder before running the code.
FO = "C:\\Fred_NB\\FinalOutputs"

#Manually install the plugin NNJoin in QGIS
    #Plugins --> Manage and Install Plugins --> search for NNjoin and install
    

###########################################
#Load data and generate 1 km2 grid
###########################################
#Remove all current layers
QgsProject.instance().clear()

#Open and display a vector layer
    #iface.addVectorLayer(data_source, layer_name, provider_name)
layerCT = iface.addVectorLayer(CT, 'CensusTract','ogr')
layerDB = iface.addVectorLayer(DB, 'DissemninationBlock','ogr')
layerBF = iface.addVectorLayer(BF, 'BuildingFootprints','ogr')

#Create a 1 km2 grid using the extent of input CT
CT_Ext = layerCT.extent()
ext = str(CT_Ext.xMinimum()) +','+ str(CT_Ext.xMaximum()) +','+ str(CT_Ext.yMinimum())+','+ str(CT_Ext.yMaximum())
crs = '['+ layerCT.crs().authid() +']'
processing.run("qgis:creategrid", 
    {'TYPE':2,'EXTENT':ext+' '+crs,
    'HSPACING':1000,'VSPACING':1000,'HOVERLAY':0,'VOVERLAY':0,
    'CRS':QgsCoordinateReferenceSystem(layerCT.crs().authid()),'OUTPUT':TEMP+'\\GRID.shp'})

print("Loaded input data loaded and created 1 km2 grid")

###########################################
#Validate and preprocess the input data       
###########################################

#Fix geometries of the input data files
processing.run("native:fixgeometries", {'INPUT': BF,'OUTPUT': TEMP+'\\BF_fixed.shp'})
processing.run("native:fixgeometries", {'INPUT': CT,'OUTPUT': TEMP+'\\CT_fixed.shp'})
processing.run("native:fixgeometries", {'INPUT': DB,'OUTPUT': TEMP+'\\DB_fixed.shp'})

#Clip BF to CT's extent
processing.run("native:clip",{'INPUT':TEMP+'\\BF_fixed.shp','OVERLAY':TEMP+'\\CT_fixed.shp','OUTPUT':TEMP+'\\BF_clipped.shp'})

#Add geometry attributes (area and perimeter) to CT, DB, and GRID
processing.run("qgis:exportaddgeometrycolumns", {'INPUT':TEMP+'\\CT_fixed.shp','CALC_METHOD':0,'OUTPUT':TEMP+'\\CT_geom.shp'})
processing.run("qgis:exportaddgeometrycolumns", {'INPUT':TEMP+'\\DB_fixed.shp','CALC_METHOD':0,'OUTPUT':TEMP+'\\DB_geom.shp'})
processing.run("qgis:exportaddgeometrycolumns", {'INPUT':TEMP+'\\GRID.shp','CALC_METHOD':0,'OUTPUT':TEMP+'\\GRID_geom.shp'})

#Drop unnecessary fields in the input data to speed up processing
processing.run("qgis:deletecolumn", 
    {'INPUT':TEMP+'\\BF_fixed.shp',
    'COLUMN':['Longitude','Latitude','CSDUID','CSDNAME','Data_prov','Shape_Leng'],
    'OUTPUT':TEMP+'\\BF_clean.shp'})

processing.run("qgis:deletecolumn", 
    {'INPUT':TEMP+'\\CT_geom.shp',
    'COLUMN':['CTNAME','PRUID','CMAUID','CMAPUID','perimeter'],
    'OUTPUT':TEMP+'\\CT_clean.shp'})

processing.run("qgis:deletecolumn", 
    {'INPUT':TEMP+'\\DB_geom.shp',
    'COLUMN':['DBRPLAMX','DBRPLAMY','PRUID','CDUID','CDNAME','CDTYPE','CCSUID','CCSNAME','CSDUID','CSDNAME','CSDTYPE','ERUID','ERNAME','FEDUID','FEDNAME','SACCODE','SACTYPE','CMAUID','CMAPUID','CTUID','CTNAME','ADAUID','DAUID','perimeter'],
    'OUTPUT':TEMP+'\\DB_clean.shp'})
    
processing.run("qgis:deletecolumn", 
    {'INPUT':TEMP+'\\GRID_geom.shp',
    'COLUMN':['left','top','right','bottom','perimeter'],
    'OUTPUT':TEMP+'\\GRID_clean.shp'})
print("Validated and preprocessed input data")

###########################################
#Edge distance between nearest buildings 
###########################################
NNJoinLayer= iface.addVectorLayer(TEMP+'\\BF_clean.shp','NNJoinLayer','ogr')

#Shortly after executing the code, the NNJoin window will pop out.
#Make sure you have installed the plugin NNJoin in QGIS
    #Plugins --> Manage and Install Plugins --> search for NNjoin and install
#Prompt the user to set the parameters as follows
print("--------------------------")
print("In the NNJoin pop-out window, set the parameters as follows")
print("Input vector layer:NNJoinLayer BF_clean")
print("Join vector layer:NNJoinLayer BF_clean")
print("Join prefix:nearest_")
print("Output layer:BF_NNJoin")
print("LEAVE ALL THE OTHER PARAMETERS AS DEFAULT")
print("Click OK")
print("--------------------------")
print("The rest of the Python script will be automatically executed after NNJoin is completed.")

import NNJoin
#Run the following commands to identify what function we should run in this plugin
    #help(NNJoin)
from qgis.utils import plugins
    #dir (plugins['NNJoin'])
plugins['NNJoin'].run()

#Save the result layer to shapefile
NNJoin_Result = QgsProject.instance().mapLayersByName("BF_NNJoin")[0]
QgsVectorFileWriter.writeAsVectorFormat(NNJoin_Result, TEMP+ "\\BF_NNJoin.shp", "utf-8", NNJoin_Result.crs(), "ESRI Shapefile")

#Remove layers
QgsProject.instance().layerTreeRoot().removeLayer(NNJoinLayer)
QgsProject.instance().layerTreeRoot().removeLayer(NNJoin_Result)

print("Computed edge distance between nearest buildings")

###########################################
#Calculate average size (AvgSize)      
###########################################

#CT_AvgSize.shp
processing.run("qgis:joinbylocationsummary", 
    {'INPUT':TEMP+'\\CT_clean.shp','JOIN':TEMP+'\\BF_clean.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['Shape_Area'],'SUMMARIES':[6],'DISCARD_NONMATCHING':True,
    'OUTPUT':TEMP+'\\CT_AvgSize.shp'})
#Load the output shapefile as a layer and rename the field
    #renameAttribute(self, index: int, newName: str)
    #and then remove TempLayer
TempLayer= iface.addVectorLayer(TEMP+'\\CT_AvgSize.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())  #the index of the field to be renamed
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'AvgSize')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)

#DB_AvgSize.shp
processing.run("qgis:joinbylocationsummary", 
    {'INPUT':TEMP+'\\DB_clean.shp','JOIN':TEMP+'\\BF_clean.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['Shape_Area'],'SUMMARIES':[6],'DISCARD_NONMATCHING':True,
    'OUTPUT':TEMP+'\\DB_AvgSize.shp'})
TempLayer= iface.addVectorLayer(TEMP+'\\DB_AvgSize.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'AvgSize')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)

#GRID_AvgSize.shp
processing.run("qgis:joinbylocationsummary", 
    {'INPUT':TEMP+'\\GRID_clean.shp','JOIN':TEMP+'\\BF_clean.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['Shape_Area'],'SUMMARIES':[6],'DISCARD_NONMATCHING':True,
    'OUTPUT':TEMP+'\\GRID_AvgSize.shp'})
TempLayer= iface.addVectorLayer(TEMP+'\\GRID_AvgSize.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'AvgSize')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)

print("Calculated average size (AvgSize)")

###########################################
#Calculate building density (BD)      
###########################################

#Calculate building count by CT
processing.run("qgis:joinbylocationsummary", 
    {'INPUT':TEMP+'\\CT_AvgSize.shp','JOIN':TEMP+'\\BF_clean.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['Build_ID'],'SUMMARIES':[0],'DISCARD_NONMATCHING':False,
    'OUTPUT':TEMP+'\\CT_AvgSize_BldgCount.shp'})
#Rename the field
TempLayer= iface.addVectorLayer(TEMP+'\\CT_AvgSize_BldgCount.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())  #the index of the field to be renamed
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'BldgCount')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)
#Calculate BD by CT
processing.run("qgis:fieldcalculator", 
    {'INPUT':TEMP+'\\CT_AvgSize_BldgCount.shp',
    'FIELD_NAME':'BD','FIELD_TYPE':0,'FIELD_LENGTH':12,'FIELD_PRECISION':8,'NEW_FIELD':True,'FORMULA':'BldgCount / area',
    'OUTPUT':TEMP+'\\CT_AvgSize_BD.shp'})

#Calculate building count by DB
processing.run("qgis:joinbylocationsummary", 
    {'INPUT':TEMP+'\\DB_AvgSize.shp','JOIN':TEMP+'\\BF_clean.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['Build_ID'],'SUMMARIES':[0],'DISCARD_NONMATCHING':False,
    'OUTPUT':TEMP+'\\DB_AvgSize_BldgCount.shp'})
#Rename the field
TempLayer= iface.addVectorLayer(TEMP+'\\DB_AvgSize_BldgCount.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'BldgCount')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)
#Calculate BD by DB
processing.run("qgis:fieldcalculator", 
    {'INPUT':TEMP+'\\DB_AvgSize_BldgCount.shp',
    'FIELD_NAME':'BD','FIELD_TYPE':0,'FIELD_LENGTH':12,'FIELD_PRECISION':8,'NEW_FIELD':True,'FORMULA':'BldgCount / area',
    'OUTPUT':TEMP+'\\DB_AvgSize_BD.shp'})
    
#Calculate building count by GRID
processing.run("qgis:joinbylocationsummary", 
    {'INPUT':TEMP+'\\GRID_AvgSize.shp','JOIN':TEMP+'\\BF_clean.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['Build_ID'],'SUMMARIES':[0],'DISCARD_NONMATCHING':False,
    'OUTPUT':TEMP+'\\GRID_AvgSize_BldgCount.shp'})
#Rename the field
TempLayer= iface.addVectorLayer(TEMP+'\\GRID_AvgSize_BldgCount.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'BldgCount')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)
#Calculate BD by GRID
processing.run("qgis:fieldcalculator", 
    {'INPUT':TEMP+'\\GRID_AvgSize_BldgCount.shp',
    'FIELD_NAME':'BD','FIELD_TYPE':0,'FIELD_LENGTH':12,'FIELD_PRECISION':8,'NEW_FIELD':True,'FORMULA':'BldgCount / area',
    'OUTPUT':TEMP+'\\GRID_AvgSize_BD.shp'})

print("Calculated building density (BD)")

###########################################
#Calculate building coverage ratio (BCR)
###########################################

#Calculate BCR by CT
#Calculate SumBldgArea by CT
processing.run("qgis:joinbylocationsummary", 
    {'INPUT': TEMP+'\\CT_AvgSize_BD.shp','JOIN':TEMP+'\\BF_clean.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['Shape_Area'],'SUMMARIES':[5],'DISCARD_NONMATCHING':True,
    'OUTPUT':TEMP+'\\CT_SumBldgArea.shp'})
#Rename the field
TempLayer= iface.addVectorLayer(TEMP+'\\CT_SumBldgArea.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'BldgArea')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)
#Divide SumBldgArea by the area of CT
processing.run("qgis:fieldcalculator", 
    {'INPUT':TEMP+'\\CT_SumBldgArea.shp',
    'FIELD_NAME':'BCR','FIELD_TYPE':0,'FIELD_LENGTH':12,'FIELD_PRECISION':8,'NEW_FIELD':True,'FORMULA':'BldgArea / area',
    'OUTPUT':TEMP+'\\CT_AvgSize_BD_BCR.shp'})

#Calculate BCR by DB
processing.run("qgis:joinbylocationsummary", 
    {'INPUT': TEMP+'\\DB_AvgSize_BD.shp','JOIN':TEMP+'\\BF_clean.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['Shape_Area'],'SUMMARIES':[5],'DISCARD_NONMATCHING':True,
    'OUTPUT':TEMP+'\\DB_SumBldgArea.shp'})
TempLayer= iface.addVectorLayer(TEMP+'\\DB_SumBldgArea.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'BldgArea')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)
processing.run("qgis:fieldcalculator", 
    {'INPUT':TEMP+'\\DB_SumBldgArea.shp',
    'FIELD_NAME':'BCR','FIELD_TYPE':0,'FIELD_LENGTH':12,'FIELD_PRECISION':8,'NEW_FIELD':True,'FORMULA':'BldgArea / area',
    'OUTPUT':TEMP+'\\DB_AvgSize_BD_BCR.shp'})

#Calculate BCR by GRID
processing.run("qgis:joinbylocationsummary", 
    {'INPUT': TEMP+'\\GRID_AvgSize_BD.shp','JOIN':TEMP+'\\BF_clean.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['Shape_Area'],'SUMMARIES':[5],'DISCARD_NONMATCHING':True,
    'OUTPUT':TEMP+'\\GRID_SumBldgArea.shp'})
TempLayer= iface.addVectorLayer(TEMP+'\\GRID_SumBldgArea.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'BldgArea')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)
processing.run("qgis:fieldcalculator", 
    {'INPUT':TEMP+'\\GRID_SumBldgArea.shp',
    'FIELD_NAME':'BCR','FIELD_TYPE':0,'FIELD_LENGTH':12,'FIELD_PRECISION':8,'NEW_FIELD':True,'FORMULA':'BldgArea / area',
    'OUTPUT':TEMP+'\\GRID_AvgSize_BD_BCR.shp'})

print("Calculated building coverage ratio (BCR)")

###########################################
#Calculate building proximity (ProxMean)      
###########################################

#Calculate ProxMean by CT
processing.run("qgis:joinbylocationsummary", 
    {'INPUT':TEMP+'\\CT_AvgSize_BD_BCR.shp','JOIN':TEMP+'\\BF_NNJoin.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['distance'],'SUMMARIES':[6],'DISCARD_NONMATCHING':False,
    'OUTPUT':TEMP+'\\CT_AvgSize_BD_BCR_Prox.shp'})
#Rename the field
TempLayer= iface.addVectorLayer(TEMP+'\\CT_AvgSize_BD_BCR_Prox.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'ProxMean')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)

#Calculate ProxMean by DB
processing.run("qgis:joinbylocationsummary", 
    {'INPUT':TEMP+'\\DB_AvgSize_BD_BCR.shp','JOIN':TEMP+'\\BF_NNJoin.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['distance'],'SUMMARIES':[6],'DISCARD_NONMATCHING':False,
    'OUTPUT':TEMP+'\\DB_AvgSize_BD_BCR_Prox.shp'})
TempLayer= iface.addVectorLayer(TEMP+'\\DB_AvgSize_BD_BCR_Prox.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'ProxMean')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)

#Calculate ProxMean by GRID
processing.run("qgis:joinbylocationsummary", 
    {'INPUT':TEMP+'\\GRID_AvgSize_BD_BCR.shp','JOIN':TEMP+'\\BF_NNJoin.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['distance'],'SUMMARIES':[6],'DISCARD_NONMATCHING':False,
    'OUTPUT':TEMP+'\\GRID_AvgSize_BD_BCR_Prox.shp'})
TempLayer= iface.addVectorLayer(TEMP+'\\GRID_AvgSize_BD_BCR_Prox.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'ProxMean')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)

print("Calculated building proximity (ProxMean)")

###########################################
#Calculate building contiguity (ContRatio)    
###########################################

#Select distance <= 1m in BF_NNJoin.shp and save as a new shapefile
TempLayer= iface.addVectorLayer(TEMP+'\\BF_NNJoin.shp','TempLayer','ogr')
TempLayer.selectByExpression('"distance" <= 1', QgsVectorLayer.SetSelection)
QgsVectorFileWriter.writeAsVectorFormat(
    TempLayer, TEMP+'\\BF_NNJoin1m.shp', 'System', 
    QgsCoordinateReferenceSystem(TempLayer.crs().authid()), 'ESRI Shapefile', onlySelected=True)
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)

#Calculate ContRatio by CT
#Count contiguous buildings (distance <= 1m) by CT
processing.run("qgis:joinbylocationsummary", 
    {'INPUT':TEMP+'\\CT_AvgSize_BD_BCR_Prox.shp','JOIN':TEMP+'\\BF_NNJoin1m.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['Build_ID'],'SUMMARIES':[0],'DISCARD_NONMATCHING':False,
    'OUTPUT':TEMP+'\\CT_ContCount.shp'})
#Rename the field
TempLayer= iface.addVectorLayer(TEMP+'\\CT_ContCount.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'ContCount')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)
#Calculate ContRatio by CT
processing.run("qgis:fieldcalculator", 
    {'INPUT':TEMP+'\\CT_ContCount.shp',
    'FIELD_NAME':'ContRatio','FIELD_TYPE':0,'FIELD_LENGTH':12,'FIELD_PRECISION':8,'NEW_FIELD':True,
    'FORMULA':'ContCount / BldgCount', 'OUTPUT':FO+'\\CT_Stats.shp'})

#Calculate ContRatio by DB
processing.run("qgis:joinbylocationsummary", 
    {'INPUT':TEMP+'\\DB_AvgSize_BD_BCR_Prox.shp','JOIN':TEMP+'\\BF_NNJoin1m.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['Build_ID'],'SUMMARIES':[0],'DISCARD_NONMATCHING':False,
    'OUTPUT':TEMP+'\\DB_ContCount.shp'})
TempLayer= iface.addVectorLayer(TEMP+'\\DB_ContCount.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'ContCount')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)
processing.run("qgis:fieldcalculator", 
    {'INPUT':TEMP+'\\DB_ContCount.shp',
    'FIELD_NAME':'ContRatio','FIELD_TYPE':0,'FIELD_LENGTH':12,'FIELD_PRECISION':8,'NEW_FIELD':True,
    'FORMULA':'ContCount / BldgCount', 'OUTPUT':FO+'\\DB_Stats.shp'})
    
#Calculate ContRatio by GRID
processing.run("qgis:joinbylocationsummary", 
    {'INPUT':TEMP+'\\GRID_AvgSize_BD_BCR_Prox.shp','JOIN':TEMP+'\\BF_NNJoin1m.shp',
    'PREDICATE':[1],'JOIN_FIELDS':['Build_ID'],'SUMMARIES':[0],'DISCARD_NONMATCHING':False,
    'OUTPUT':TEMP+'\\GRID_ContCount.shp'})
TempLayer= iface.addVectorLayer(TEMP+'\\GRID_ContCount.shp','TempLayer','ogr')
idx = max(TempLayer.attributeList())
with edit(TempLayer):
    TempLayer.renameAttribute(idx, 'ContCount')
QgsProject.instance().layerTreeRoot().removeLayer(TempLayer)
processing.run("qgis:fieldcalculator", 
    {'INPUT':TEMP+'\\GRID_ContCount.shp',
    'FIELD_NAME':'ContRatio','FIELD_TYPE':0,'FIELD_LENGTH':12,'FIELD_PRECISION':8,'NEW_FIELD':True,
    'FORMULA':'ContCount / BldgCount', 'OUTPUT':FO+'\\GRID_Stats.shp'})

print("Calculated building contiguity (Contiguity)")

###########################################
#Load the final outputs into QGIS  
###########################################
iface.addVectorLayer(FO+'\\CT_Stats.shp','','ogr')
iface.addVectorLayer(FO+'\\DB_Stats.shp','','ogr')
iface.addVectorLayer(FO+'\\GRID_Stats.shp','','ogr')
print("All completed.")