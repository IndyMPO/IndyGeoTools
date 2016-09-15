import arcpy
from numpy import array

taz_file = arcpy.GetParameterAsText(0) #Shapefile
hh_field = arcpy.GetParameterAsText(1) #Field in TAZ file
ej_list = arcpy.GetParameterAsText(2) #Text file with list of EJ TAZs
outfile = arcpy.GetParameterAsText(3) #Output text file. It must be created to run, but it can be blank

#Check if the file containing the list of EJ TAZs and the output file are the same. If they are, raise an error.
if ej_list == outfile:
    raise IOError('List of EJ TAZs and output file are the same')

#Check to make sure that the accessibility calculator has been run by seeing if accessibility fields are in the TAZ file
fields = [field.name for field in arcpy.ListFields(taz_file)]
if 'ACC_RET' not in fields or 'ACC_NRE' not in fields or 'TRN_ACC' not in fields:
    raise IOError('Must run Accessibility Calculator before running this tool')

#Read in list of EJ TAZs
with open(ej_list, 'r') as f:
    ej_tazs = f.read().split('\n')

#Start weighted average totals at zero
ej_auto_num = 0
ej_transit_num = 0
ej_hh = 0
non_auto_num = 0
non_transit_num = 0
non_hh = 0

#Loop to calculate weighted average numerators and denomenators
tazs = arcpy.da.SearchCursor(taz_file, field_names = ['TAZ', hh_field, 'ACC_RET', 'ACC_NRE', 'TRN_ACC'])
for taz in tazs:

    #If a TAZ is an EJ TAZ, add data for the EJ averages
    if str(taz[0]) in ej_tazs:
        ej_auto_num += taz[1]*(taz[2] + taz[3])
        ej_transit_num += taz[1]*taz[4]
        ej_hh += taz[1]

    #Otherwise, add data for non-EJ averages
    else:
        non_auto_num += taz[1]*(taz[2] + taz[3])
        non_transit_num += taz[1]*taz[4]
        non_hh += taz[1]

#Compute averages
try:
    ej_auto = float(ej_auto_num) / ej_hh
    ej_transit = float(ej_transit_num) / ej_hh
    non_auto = float(non_auto_num) / non_hh
    non_transit = float(non_transit_num) / non_hh

#If one group has zero households, indicate which group does, and say so on the output file
except ZeroDivisionError:
    lines = []
    if not ej_hh:
        lines.append('There are no households in EJ TAZs')
    if not non_hh:
        lines.append('There are no households in non-EJ TAZs')

    with open(outfile, 'w') as f:
        f.write('\n'.join(lines))
    f.close()

#If both groups have households, record the averages as well as their differences in the output file
finally:
    auto_diff = non_auto - ej_auto
    transit_diff = non_transit - ej_transit

    lines = []
    lines.append('Non-EJ average job auto accessibility: {}'.format(round(non_auto, 3)))
    lines.append('EJ average job auto accessibility: {}'.format(round(ej_auto, 3)))
    lines.append('Difference: {}'.format(round(auto_diff, 3)))

    lines.append('\n') #Blank line to separate auto and transit

    lines.append('Non-EJ average job transit accessibility: {}'.format(round(non_transit, 3)))
    lines.append('EJ average job transit accessibility: {}'.format(round(ej_transit, 3)))
    lines.append('Difference: {}'.format(round(transit_diff, 3)))

    with open(outfile, 'w') as f:
        f.write('\n'.join(lines))
    f.close()
