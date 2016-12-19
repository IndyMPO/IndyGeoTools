#This script copyright 2017 Indianapolis Metropolitan Planning Organization
__version__ = '1.0'

import arcpy
import os
import pandas as pd
import numpy as np
from subprocess import Popen
import sys

def clear_temp():
    '''
    Clears the temporary directory that is created when running this tool
    '''
    temp_dir = r'C:\TEMP'
    for f in os.listdir(temp_dir): #Remove all files within the directory
        os.remove(os.path.join(temp_dir, f))
    os.rmdir(temp_dir) #Remove the directory itself

#Read in inputs
from_shp_file = arcpy.GetParameterAsText(0)
from_field = arcpy.GetParameterAsText(1)
to_shp_file = arcpy.GetParameterAsText(2)
to_field = arcpy.GetParameterAsText(3)
outfile = arcpy.GetParameterAsText(4)
show_matrix = arcpy.GetParameter(5)
remove_temp_if_successful = arcpy.GetParameter(6)
remove_temp_if_error = arcpy.GetParameter(7)

#Check if the outfile is specified as a csv file. If it isn't, do so.
if outfile[-4:] != '.csv':
    outfile += '.csv'

#Create temporary directory
temp_dir = r'C:\TEMP'
os.mkdir(temp_dir)
temp_shp = os.path.join(temp_dir, 'TEMP.shp')
from_shp = os.path.join(temp_dir, 'FROM.shp')
to_shp = os.path.join(temp_dir, 'TO.shp')

#Copy input shapefiles into temporary directory
arcpy.CopyFeatures_management(from_shp_file, from_shp)
arcpy.CopyFeatures_management(to_shp_file, to_shp)

#Process the data. If an error occurs, the temporary directory will be deleted, and then the exception will be raised
try:

    #Intersect the two shapefiles and calculate the area of the intersected shapefile
    arcpy.Intersect_analysis([from_shp, to_shp], temp_shp)
    temp2_shp = temp_shp.replace('.shp', '2.shp')
    arcpy.CalculateAreas_stats(temp_shp, temp2_shp)

    #Create a list of all of the origin and destination polygons
    from_list = []
    to_list = []
    polygons = arcpy.da.SearchCursor(temp_shp, [from_field, to_field])
    for polygon in polygons:
        from_list += [polygon[0]]
        to_list += [polygon[1]]
    del polygons

    from_codes = pd.Series(from_list).value_counts().index
    to_codes = pd.Series(to_list).value_counts().index

    #Create matrix with total area of each intersected polygon, arranged by the from polygon and to polygon
    areas = pd.DataFrame(np.zeros((len(to_codes), len(from_codes))), index = to_codes, columns = from_codes)
    polygons = arcpy.da.SearchCursor(temp2_shp, [from_field, to_field, 'F_AREA'])
    for polygon in polygons:
        areas.loc[polygon[1], polygon[0]] = polygon[2]
    del polygons

    #Divide each column of the matrix by its sum
    total = areas.sum(0)
    out_data = areas.copy()
    for row in out_data.index:
        out_data.loc[row] /= total

    #Write to csv, and delete the temporary directory
    out_data.to_csv(outfile)
    if remove_temp_if_successful:
        clear_temp()

except Exception as e:
    if remove_temp_if_error:
        clear_temp()
    exc_type, exc_obj, exc_tb = sys.exc_info()
    print (exc_tb.tb_lineno)
    raise e

#Open the file if instructed to do so
if show_matrix:
    Popen(outfile, shell = True)
