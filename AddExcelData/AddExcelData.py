#This script copyright 2017 Indianapolis Metropolitan Planning Organization
import arcpy
import pandas as pd

shapefile = arcpy.GetParameterAsText(0)
id_field = arcpy.GetParameterAsText(1)
excel_file = arcpy.GetParameterAsText(2)
sheet = arcpy.GetParameter(3)

#Map to determine each new field's data type based on the data frame's column's data type
dtype_map = {'int64': 'LONG',
             'float32': 'FLOAT',
             'float64': 'DOUBLE'}

#Read in data
data = pd.read_excel(excel_file, sheet, index_col = 0)

#Add fields based on columns of the table
new_fields = []
for col in data.columns:
    #new_field = sheet + col
    new_field = col
    arcpy.AddMessage(new_field)
    new_fields += [new_field]
    if new_field not in [field.name for field in arcpy.ListFields(shapefile)]:
        arcpy.AddField_management(shapefile, new_field, dtype_map[str(data[col].dtype)], field_is_nullable = True)

#Write values in data frame to attribute table
rows = arcpy.da.UpdateCursor(shapefile, field_names = [id_field] + new_fields)
for row in rows:
    try:
        for i in range(len(new_fields)):
            row[i+1] = data[data.columns[i]][row[0]]
        rows.updateRow(row)
    except KeyError:
        arcpy.AddMessage('WARNING: Data for "{}" is not present in the Excel file.'.format(row[0]))
del row
del rows
