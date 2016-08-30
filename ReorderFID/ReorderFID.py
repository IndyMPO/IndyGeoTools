import arcpy
import json

data_file = arcpy.GetParameterAsText(0)
map_file = arcpy.GetParameterAsText(1)

#data_file = 'C:/IndyLUM/Model/Inputs/ZONES.dbf'
#map_file = 'H:/TAZ_FID_MAP.json'
try:
    arcpy.Delete_management(data_file[:-4] + '_BACKUP.shp')
except Exception:
    pass
arcpy.CopyFeatures_management(data_file, data_file[:-4] + '_BACKUP.shp')

arcpy.AddMessage('Reading in dictionary')
taz_fid_map = json.load(open(map_file, 'r'))

field_map = {}
row_map = {}

arcpy.AddMessage('Identifying TAZ field index')
fields = [field.name for field in arcpy.ListFields(data_file)]
for i in range(len(fields)):
    if fields[i] == 'TAZ':
        taz_index = i
        break

arcpy.AddMessage('Obtaining data from each TAZ')
data = {}
rows = arcpy.da.SearchCursor(data_file, field_names = fields)
for row in rows:
    taz = row[taz_index]
    data[taz] = list(row[1:])

arcpy.AddMessage('Writing correct TAZ data to each polygon')
rows = arcpy.da.UpdateCursor(data_file, field_names = fields)
for row in rows:
    taz = taz_fid_map[unicode(row[0])]
    for i in range(1, len(fields)):
        row[i] = data[taz][i-1]
    rows.updateRow(row)
del row
del rows
