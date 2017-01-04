#This script copyright 2017 Indianapolis Metropolitan Planning Organization
import arcpy
import os

temp_dir = r'C:\CountAssumedTransitStops' #Directory to temporarly store intermediate shapefiles

def clear_temp():
    '''
    Clears the temporary directory
    '''
    global temp_dir
    for f in os.listdir(temp_dir): #Remove each file individually
        os.remove(os.path.join(temp_dir, f))
    os.rmdir(temp_dir) #Remove the directory

#Read in inputs
polygon_file = arcpy.GetParameterAsText(0)
id_field = arcpy.GetParameterAsText(1)
route_file = arcpy.GetParameterAsText(2)
assumed_lane_width = arcpy.GetParameterAsText(3)
assumed_stop_spacing = arcpy.GetParameterAsText(4).split(' ')
new_field = arcpy.GetParameterAsText(5)
return_integer = arcpy.GetParameter(6)
remove_temp_if_successful = arcpy.GetParameter(7)
remove_temp_if_error = arcpy.GetParameter(8)

#Extract data from inputs
lane_width = float(assumed_lane_width.split(' ')[0])
spacing = float(assumed_stop_spacing[0])
units = assumed_stop_spacing[1]

assert assumed_lane_width.split(' ')[1] == units, 'Lane width and stop spacing must have the same units'

#Create temporary directory and define temporary files
os.mkdir(temp_dir)
buffer_shp = os.path.join(temp_dir, 'BUFFER.shp')
intersect_shp = os.path.join(temp_dir, 'INTERSECTED.shp')
area_shp = os.path.join(temp_dir, 'AREA.shp')

try:
    arcpy.AddMessage('Creating Temporary Shapefiles')
    if arcpy.ProductInfo() == 'ArcInfo':
        arcpy.Buffer_analysis(route_file, buffer_shp, assumed_lane_width, dissolve_option = 'ALL', line_side = 'RIGHT', line_end_type = 'FLAT')
    else:
        arcpy.AddMessage('WARNING: Results will be more accurate with ArcInfo license')
        arcpy.Buffer_analysis(route_file, buffer_shp, assumed_lane_width, dissolve_option = 'ALL')
    arcpy.Intersect_analysis([polygon_file, buffer_shp], intersect_shp)
    arcpy.CalculateAreas_stats(intersect_shp, area_shp)

    arcpy.AddMessage('Approximating Stops By Polygon')
    stops = {}
    polygons = arcpy.da.SearchCursor(area_shp, field_names = [id_field, 'F_AREA'])
    for polygon in polygons:
        if polygon[0] not in stops:
            stops[polygon[0]] = 0
        stops[polygon[0]] += polygon[1] / (lane_width * spacing)
    del polygons

    arcpy.AddMessage('Adding Approximate Number of Stops to Polygon File')
    if new_field in [field.name for field in arcpy.ListFields(polygon_file)]:
        arcpy.DeleteField_management(polygon_file, new_field)
    if return_integer:
        arcpy.AddField_management(polygon_file, new_field, 'LONG')
    else:
        arcpy.AddField_management(polygon_file, new_field, 'DOUBLE')

    polygons = arcpy.da.UpdateCursor(polygon_file, field_names = [id_field, new_field])
    for polygon in polygons:
        try:
            if return_integer:
                polygon[1] = int(stops[polygon[0]])
            else:
                polygon[1] = stops[polygon[0]]
            polygons.updateRow(polygon)
        except KeyError:
            continue
    del polygon
    del polygons

except Exception as e:
    if remove_temp_if_error:
        clear_temp()
    raise Exception(e)

if remove_temp_if_successful:
    clear_temp()
