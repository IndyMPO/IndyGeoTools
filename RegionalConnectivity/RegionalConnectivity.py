import arcpy
import numpy as np

taz_file = arcpy.GetParameterAsText(0)
skim_file = arcpy.GetParameterAsText(1)
taz_subset_file = arcpy.GetParameterAsText(2)
output_file = arcpy.GetParameterAsText(3)
new_field_suffix = arcpy.GetParameterAsText(4)

if not new_field_suffix:
    new_field_suffix = ''

assert len(new_field_suffix) <= 5, 'New field prefix must be at most two characters long'

assert 'TAZ' in [field.name for field in arcpy.ListFields(taz_file)], 'TAZ file must contain field with name "TAZ"'

def extract_skim_from_csv(csv_file):
    '''
    Reads in a skim with labels as a csv and returns a 2-dimensional numpy array and a dictionary mapping zone to array index

    Parameters
    ----------
    csv_file (str):
        Filepath of the csv to read in
    '''
    data = np.genfromtxt(csv_file, delimiter = ',', filling_values = np.inf) #Read in data
    zones = data[0, :]
    zone_map = {zones[i+1]: i for i in range(len(zones)-1)} #Create dictionary for mapping zones
    skim = data[1:, 1:] #Define actual skim data
    return skim, zone_map



def create_subskim(skim, zone_map, subset_zones):
    indices = []
    for zone in subset_zones:
        indices.append(zone_map[int(zone)])
    subskim = skim[:, indices][indices]
    subzone_map = {subset_zones[i]: i for i in range(len(subset_zones))}
    return subskim, subzone_map



arcpy.AddMessage('Adding new fields')
new_fields = ['AVIN' + new_field_suffix,
              'AVOUT' + new_field_suffix,
              'SEIN' + new_field_suffix,
              'SEOUT' + new_field_suffix]
for field in new_fields:
    try:
        arcpy.DeleteField_management(taz_file, field)
    except Exception:
        continue
    arcpy.AddField_management(taz_file, field, 'DOUBLE')

arcpy.AddMessage('Reading in skim: ' + skim_file)
(skim, zone_map) = extract_skim_from_csv(skim_file)

arcpy.AddMessage('Creating subskim from ' + taz_subset_file)
zones = open(taz_subset_file, 'r').read().split('\n')
(subskim, subzone_map) = create_subskim(skim, zone_map, zones)
N = len(zones)

arcpy.AddMessage('Calculating average travel times')
tazs = arcpy.da.UpdateCursor(taz_file, field_names = ['TAZ'] + new_fields)
for taz in tazs:
    if str(taz[0]) in zones:
        zoneno = str(taz[0])
        taz[1] = subskim[:, subzone_map[zoneno]].mean()
        taz[2] = subskim[subzone_map[zoneno], :].mean()
        taz[3] = np.sqrt((subskim[:, subzone_map[zoneno]]).var()/N)
        taz[4] = np.sqrt((subskim[subzone_map[zoneno], :]).var()/N)
        tazs.updateRow(taz)
    else:
        continue

avg = subskim.mean().mean()
se = np.sqrt(np.reshape(subskim, N*N).var())/N

results = ['Average = %f'%(avg), 'Standard Error = %f'%(se)]

arcpy.AddMessage('Writing Output File')
open(output_file, 'w').write('\n'.join(results))

arcpy.AddMessage(' ')
arcpy.AddMessage(results[0])
arcpy.AddMessage(results[1])

