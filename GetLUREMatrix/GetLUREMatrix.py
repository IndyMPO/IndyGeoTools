import arcpy
from arcpy.mapping import Layer as lyr
import os
from collections import OrderedDict
from subprocess import Popen
import numpy as np

parcel_point_file = arcpy.GetParameterAsText(0)
re_col = arcpy.GetParameterAsText(1)
area_col = arcpy.GetParameterAsText(2)
lu_polygon_file = arcpy.GetParameterAsText(3)
lu_col = arcpy.GetParameterAsText(4)
joined_shp_file = arcpy.GetParameterAsText(5)
outfile = arcpy.GetParameterAsText(6)

if joined_shp_file[-4:] != '.shp':
    joined_shp_file += '.shp'
if outfile[-4:] != '.csv':
    outfile += '.csv'

arcpy.AddMessage('Selecting Points within Jurisdiction')

parcel_points = lyr(parcel_point_file)
selection = arcpy.SelectLayerByLocation_management(parcel_points, 'WITHIN', lyr(lu_polygon_file))

arcpy.AddMessage('Creating Layer From Selection')

tempdir = r'C:\GetRELUMatrix'
os.mkdir(tempdir)
tempfile = os.path.join(tempdir, 'TEMP.shp')
arcpy.CopyFeatures_management(parcel_points, tempfile)

arcpy.AddMessage('Joining Parcels to Zoning')

arcpy.SpatialJoin_analysis(tempfile, lu_polygon_file, joined_shp_file, match_option = 'WITHIN')
arcpy.AddMessage('Deleting Temporary File')
for f in os.listdir(tempdir):
    os.remove(os.path.join(tempdir, f))
os.rmdir(tempdir)

arcpy.AddMessage('Aggregating Data')

units = {}
total = {}

parcels = arcpy.da.SearchCursor(joined_shp_file, field_names = [re_col, area_col, lu_col])
for parcel in parcels:
    if parcel[0] == 0:
        continue

    if parcel[2] not in units:
        units[parcel[2]] = OrderedDict(zip(range(1, 13), np.zeros(12)))
        total[parcel[2]] = 0

    units[parcel[2]][parcel[0]] += parcel[1]
    total[parcel[2]] += parcel[1]



lines = [['']]
for i in range(1, 13):
    lines[0] += [str(i)]

for lu in units:
    line = [str(lu)]
    for re in units[lu]:
        try:
            line += [str(float(units[lu][re])/total[lu])]
        except ZeroDivisionError:
            line += ['0']
    lines += [line]

for i in range(len(lines)):
    lines[i] = ','.join(lines[i])

arcpy.AddMessage('Saving Matrix')

with open(outfile, 'w') as f:
    f.write('\n'.join(lines))
    f.close()

Popen(outfile, shell = True)
    
