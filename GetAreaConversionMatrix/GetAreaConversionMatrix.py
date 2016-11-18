import arcpy
import os
import pandas as pd
import numpy as np
from subprocess import Popen
import sys

def clear_temp():
    temp_dir = r'C:\TEMP'
    for f in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, f))
    os.rmdir(temp_dir)

from_shp_file = arcpy.GetParameterAsText(0)
from_field = arcpy.GetParameterAsText(1)
to_shp_file = arcpy.GetParameterAsText(2)
to_field = arcpy.GetParameterAsText(3)
outfile = arcpy.GetParameterAsText(4)
##from_shp_file = r'P:\MPO\40 RTP and Air Quality\2009_Land_Use_Model\current_LU_shapefiles\Plainfield_existing.shp'
##to_shp_file = r'P:\MPO\40 RTP and Air Quality\2009_Land_Use_Model\Future_LU_shapefiles\Plainfield.shp'
##from_field = 'LU_CODE'
##to_field = 'Land_Use'
##outfile = r'H:\Cube Land\Data\MATRIX_OUT'

if outfile[-4:] != '.csv':
    outfile += '.csv'

temp_dir = r'C:\TEMP'
os.mkdir(temp_dir)
temp_shp = os.path.join(temp_dir, 'TEMP.shp')
from_shp = os.path.join(temp_dir, 'FROM.shp')
to_shp = os.path.join(temp_dir, 'TO.shp')

arcpy.CopyFeatures_management(from_shp_file, from_shp)
arcpy.CopyFeatures_management(to_shp_file, to_shp)

try:
    arcpy.Intersect_analysis([from_shp, to_shp], temp_shp)
    temp2_shp = temp_shp.replace('.shp', '2.shp')
    arcpy.CalculateAreas_stats(temp_shp, temp2_shp)

    from_list = []
    to_list = []
    polygons = arcpy.da.SearchCursor(temp_shp, [from_field, to_field])
    for polygon in polygons:
        from_list += [polygon[0]]
        to_list += [polygon[1]]
    del polygons

    from_codes = pd.Series(from_list).value_counts().index
    to_codes = pd.Series(to_list).value_counts().index

    areas = pd.DataFrame(np.zeros((len(to_codes), len(from_codes))), index = to_codes, columns = from_codes)
    polygons = arcpy.da.SearchCursor(temp2_shp, [from_field, to_field, 'F_AREA'])
    for polygon in polygons:
        areas.loc[polygon[1], polygon[0]] = polygon[2]
    del polygons

    total = areas.sum(0)
    out_data = areas.copy()
    for row in out_data.index:
        out_data.loc[row] /= total

    out_data.to_csv(outfile)

    clear_temp()

except Exception as e:
    clear_temp()
    exc_type, exc_obj, exc_tb = sys.exc_info()
    print (exc_tb.tb_lineno)
    raise e

Popen(outfile, shell = True)
