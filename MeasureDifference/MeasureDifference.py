import arcpy

file_1 = arcpy.GetParameterAsText(0)
file_2 = arcpy.GetParameterAsText(1)
new_file = arcpy.GetParameterAsText(2)
if new_file[-4:] != '.shp':
    new_file += '.shp'
    
static_fields = arcpy.GetParameterAsText(3).split(';')

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
try:
    arcpy.CopyFeatures_management(file_1, new_file)
except Exception:
    arcpy.AddMessage('WARNING: Overwriting existing file ' + new_file)
    arcpy.Delete_management(new_file)
    arcpy.CopyFeatures_management(file_1, new_file)

new_field_method = {}
arcpy.AddMessage('Adding fields')
for field in fields_1:
    if field not in static_fields:
        arcpy.DeleteField_management(new_file, field)
        try:
            first_char = int(field[0])
            if len(field) <= 7:
                arcpy.AddField_management(new_file, '_' + field + 'D', 'DOUBLE')
                arcpy.AddField_management(new_file, '_' + field + 'PD', 'DOUBLE')
                new_field_method[field] = 0
            else:
                arcpy.AddMessage('WARNING: Truncating ' + field + ' to last 7 characters')
                arcpy.AddField_management(new_file, '_' + field[-7:] + 'D', 'DOUBLE')
                arcpy.AddField_management(new_file, '_' + field[-7:] + 'PD', 'DOUBLE')
                new_field_method[field] = 1
        except ValueError:
            if len(field) <= 6:
                arcpy.AddField_management(new_file, field + 'D', 'DOUBLE')
                arcpy.AddField_management(new_file, field + 'PD', 'DOUBLE')
                new_field_method[field] = 2
            else:
                if field[-6:] + 'D' not in [f.name for f in arcpy.ListFields(new_file)]:
                    arcpy.AddMessage('WARNING: Truncating ' + field + ' to last 8 characters')
                    arcpy.AddField_management(new_file, field[-6:] + 'D', 'DOUBLE')
                    arcpy.AddField_management(new_file, field[-6:] + 'PD', 'DOUBLE')
                    new_field_method[field] = 3
                else:
                    arcpy.AddMessage('WARNING: Truncating ' + field + ' to first 8 characters')
                    arcpy.AddField_management(new_file, field[:6] + 'D', 'DOUBLE')
                    arcpy.AddField_management(new_file, field[:6] + 'PD', 'DOUBLE')
                    new_field_method[field] = 4

new_fields = [field.name for field in arcpy.ListFields(new_file)]

arcpy.AddMessage('Reading in data')
data_1 = {}
data_2 = {}

geo_1 = arcpy.da.SearchCursor(file_1, field_names = fields_1)
for geo in geo_1:
    data_1[geo[0]] = geo
geo_2 = arcpy.da.SearchCursor(file_2, field_names = fields_2)
for geo in geo_2:
    data_2[geo[0]] = geo

arcpy.AddMessage('Calculating difference')
#cf = len(common_fields)
N = len(fields_1)
diff_geo = arcpy.da.UpdateCursor(new_file, field_names = new_fields)
for geo in diff_geo:
    gid = geo[0]
    for i in range(N):
        if fields_1[i] in static_fields:           
            new_field_index = new_fields.index(fields_1[i])
            geo[new_field_index] = data_1[gid][i]
            
        else:
            
            if new_field_method[fields_1[i]] == 0:
                new_field_index = new_fields.index('_' + fields_1[i] + 'D')
            elif new_field_method[fields_1[i]] == 1:
                new_field_index = new_fields.index('_' + fields_1[i][-7:] + 'D')
            elif new_field_method[fields_1[i]] == 2:
                new_field_index = new_fields.index(fields_1[i] + 'D')
            elif new_field_method[fields_1[i]] == 3:
                new_field_index = new_fields.index(fields_1[i][-6:] + 'D')
            else:
                new_field_index = new_fields.index(fields_1[i][:6] + 'D')

            geo[new_field_index] = data_2[gid][i] - data_1[gid][i]
            try:
                geo[new_field_index + 1] = geo[new_field_index] / data_1[gid][i]
            except ZeroDivisionError:
                geo[new_field_index + 1] = 0

    diff_geo.updateRow(geo)
del diff_geo
del geo
