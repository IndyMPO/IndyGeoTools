#This script copyright 2017 Indianapolis Metropolitan Planning Organization
__version__ = '1.0'

import arcpy
import os

file_1 = arcpy.GetParameterAsText(0)
file_2 = arcpy.GetParameterAsText(1)
new_file = arcpy.GetParameterAsText(2)
if new_file[-4:] != '.shp':
    new_file += '.shp'
    
static_fields = arcpy.GetParameterAsText(3).split(';')

key_field = arcpy.GetParameterAsText(4)
if key_field:
    key_id = [field.name for field in arcpy.ListFields(file_1)].index(key_field)
else:
    key_id = 0

proceed = False
while not proceed:
    try:
        static_fields.remove('')
    except ValueError:
        proceed = True

#Check that initial file and final file have the same fields
fields_1 = [field.name for field in arcpy.ListFields(file_1)]
fields_2 = [field.name for field in arcpy.ListFields(file_2)]
assert fields_1 == fields_2, 'Initial and final shapefiles must have the same fields'

#Check that initial file and final file have the same number of features
features_1 = int(arcpy.GetCount_management(file_1).getOutput(0))
features_2 = int(arcpy.GetCount_management(file_2).getOutput(0))
assert features_1 == features_2, 'Initial and final shapefiles must have the same number of features'

arcpy.AddMessage('Creating new file')
new_file_path = new_file.split('\\')
new_file_dir = '\\'.join(new_file_path[:-1])
if new_file_path[-1] in os.listdir(new_file_dir):
    arcpy.Delete_management(new_file)
arcpy.CopyFeatures_management(file_1, new_file)

field_truncations = {}
arcpy.AddMessage('Adding fields')
for field in fields_1:
    if field not in static_fields:
        arcpy.DeleteField_management(new_file, field)

        if len(field) <= 9:
            arcpy.AddField_management(new_file, field + 'D', 'DOUBLE')
            arcpy.AddField_management(new_file, field + 'P', 'DOUBLE')
            field_truncations[field] = False
        else:
            arcpy.AddMessage('WARNING: Removing last character from ' + field)
            arcpy.AddField_management(new_file, field[:9] + 'D', 'DOUBLE')
            arcpy.AddField_management(new_file, field[:9] + 'P', 'DOUBLE')
            field_truncations[field] = True

new_fields = [field.name for field in arcpy.ListFields(new_file)]

arcpy.AddMessage('Reading in data')
data_1 = {}
data_2 = {}

geo_1 = arcpy.da.SearchCursor(file_1, field_names = fields_1)
for geo in geo_1:
    data_1[geo[key_id]] = geo
geo_2 = arcpy.da.SearchCursor(file_2, field_names = fields_2)
for geo in geo_2:
    data_2[geo[key_id]] = geo

arcpy.AddMessage('Calculating difference')

N = len(fields_1)
diff_geo = arcpy.da.UpdateCursor(new_file, field_names = new_fields)
for geo in diff_geo:
    gid = geo[key_id]
    for i in range(N):
        if fields_1[i] in static_fields: #If the field is one of the static fields, just place it           
            new_field_index = new_fields.index(fields_1[i])
            geo[new_field_index] = data_1[gid][i]
            
        else: #Otherwise, calculate the difference and percent difference

            #Get the index of the new field based on whether or not the field name was truncated
            if field_truncations[fields_1[i]]:
                new_field_index = new_fields.index(fields_1[i][:9] + 'D')
            else:
                new_field_index = new_fields.index(fields_1[i] + 'D')

            geo[new_field_index] = data_2[gid][i] - data_1[gid][i]
            try:
                geo[new_field_index + 1] = geo[new_field_index] / data_1[gid][i]
            except ZeroDivisionError:
                geo[new_field_index + 1] = 0

    diff_geo.updateRow(geo)
del diff_geo
del geo
