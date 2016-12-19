import arcpy
import pandas as pd
import numpy as np
import os

def shp2df(shp, fields):
    '''
    Converts the attribute table in a shapefile to a Pandas data frame

    Parameters
    ----------
    shp (string):
        Filepath of the shapefile
    fields (list):
        List of fields to include

    Returns
    -------
    df (pd.DataFrame):
        Pandas data frame with the shapefile's attributes
    '''
    df = pd.DataFrame(columns = fields)
    rows = arcpy.da.SearchCursor(shp, fields)
    i = 0
    for row in rows:
        df.loc[i] = row
        i += 1

    return df

#Read in inputs
from_shp_file = arcpy.GetParameterAsText(0)
from_field = arcpy.GetParameterAsText(1)
to_shp_file = arcpy.GetParameterAsText(2)
to_field = arcpy.GetParameterAsText(3)
new_shp_file = arcpy.GetParameterAsText(4)
matrix_file = arcpy.GetParameterAsText(5)
data_fields = arcpy.GetParameterAsText(6).split(';')
remove_temp_if_successful = arcpy.GetParameter(7)
remove_temp_if_error = arcpy.GetParameter(8)

#If the new shapefile is not specified as a shapefile, do so
if new_shp_file[-4] != '.shp':
    new_shp_file += '.shp'

#Copy features from the destination shapefile to the new shapefile
arcpy.CopyFeatures_management(to_shp_file, new_shp_file)

#Check if the matrix file is specified as a csv file. If it isn't, do so.
if matrix_file[-4:] != '.csv':
    matrix_file += '.csv'


arcpy.AddMessage('Creating Area Conversion Matrix')
tbx = os.path.join(os.path.split(os.getcwd())[0], 'IndyGeoTools.tbx')
arcpy.ImportToolbox(tbx)
arcpy.GetAreaConversionMatrix_IndyGeoTools(from_shp_file, from_field, to_shp_file, to_field, matrix_file, False, remove_temp_if_successful, remove_temp_if_error)

matrix = pd.DataFrame.from_csv(matrix_file)
matrix.columns = matrix.columns.astype(float)

arcpy.AddMessage('Reading Data')
in_data = shp2df(from_shp_file, [from_field] + data_fields)
in_data = in_data.set_index(from_field)

matrix = matrix[in_data.index] #Make sure the matrix's columns are in the same order as the rows of in_data

arcpy.AddMessage('Converting Data')
out_data = pd.DataFrame(np.dot(matrix, in_data), index = matrix.index, columns = data_fields)

#Remove unnecessary fields from the new shapefile
arcpy.AddMessage('Writing Converted Data')
for field in [field.name for field in arcpy.ListFields(new_shp_file)]:
    if field not in ['FID', 'OID', 'Shape', 'Area', 'SHAPE', 'AREA'] + [to_field]:
        arcpy.DeleteField_management(new_shp_file, field)

#Add in specified fields for the new shapefile
for field in data_fields:
    arcpy.AddField_management(new_shp_file, field, 'DOUBLE')

#Write data to the new shapefile
rows = arcpy.da.UpdateCursor(new_shp_file, [to_field] + data_fields)
for row in rows:
    row[1:] = out_data.loc[row[0]]
    rows.updateRow(row)
del rows

print 'Done'
    
