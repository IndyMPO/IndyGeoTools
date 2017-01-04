#This script copyright 2017 Indianapolis Metropolitan Planning Organization
import arcpy
import numpy as np

#Read in parameters
auto_skim_file = arcpy.GetParameterAsText(0)
transit_skim_file = arcpy.GetParameterAsText(1)
auto_time_threshold = arcpy.GetParameter(2)
transit_time_threshold = arcpy.GetParameter(3)
taz_file = arcpy.GetParameterAsText(4)
taz_field = arcpy.GetParameterAsText(5)
pop_field = arcpy.GetParameterAsText(6)
emp_field = arcpy.GetParameterAsText(7)
ret_field = arcpy.GetParameterAsText(8)
accpop_name = 'ACC_POP'
accret_name = 'ACC_RET'
accnre_name = 'ACC_NRE'
attpop_name = 'ATT_POP'
attret_name = 'ATT_RET'
attnre_name = 'ATT_NRE'
trnacc_name = 'TRN_ACC'

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

def under_auto_threshold(time):
    '''
    Checks if a time is less than or equal to the auto threshold

    Parameters
    ----------
    time (numeric):
        Travel time value to be tested

    Returns
    -------
    is_under (bool):
        True if the time is less than or equal to the threshold, False otherwise
    '''
    global auto_time_threshold
    return time <= auto_time_threshold

create_auto_bool_skim = np.vectorize(under_auto_threshold)

def under_transit_threshold(time):
    '''
    Checks if a time is less than or equal to the transit threshold

    Parameters
    ----------
    time (numeric):
        Travel time value to be tested

    Returns
    -------
    is_under (bool):
        True if the time is less than or equal to the threshold, False otherwise
    '''
    global transit_time_threshold
    return time <= transit_time_threshold

create_transit_bool_skim = np.vectorize(under_transit_threshold)

def create_bool_skim(skim, threshold):
    '''
    Creates a boolean "skim" that is True if an origin-destination pair is less than or equal to a specified threshold and False otherwise

    Parameters
    ----------
    skim (ndarray):
        2-dimensional skim array
    threshold (numeric):
        Travel time threshold

    Returns
    -------
    out (ndarray):
        Array with same dimensions as input skim full of ones and zeros indicating if a pair is less than or equal to `threshold`
    '''
    out = np.empty_like(skim)
    #Iterate over rows and columns, checking each skim individually
    for i in range(skim.shape[0]):
        for j in range(skim.shape[1]):
            out[i, j] = skim[i, j] <= threshold
    return out

def calc_auto_acc(bool_skim, zone_map, taz_file):
    '''
    Calculates the number of people, retail, and non-retail jobs within a threshold of each zone. Accessibilities in the input shapefile are updated.

    Parameters
    ----------
    bool_skim (ndarray):
        2-dimensional Boolean "skim"
    zone_map (dict):
        Dictionary mapping zone number to index in the skim
    taz_file (str):
        Filepath for a TAZ shapefile
    '''
    global taz_field, pop_field, emp_field, ret_field, accpop_name, accret_name, accnre_name

    pop = np.empty_like(bool_skim, dtype = int)
    ret = np.empty_like(bool_skim, dtype = int)
    nre = np.empty_like(bool_skim, dtype = int)

    #For each zone, create ndarrays that represent the number of people, retail, and non-retail jobs that can be reached within a specific time
    zones = arcpy.da.SearchCursor(taz_file, field_names = [taz_field, pop_field, emp_field, ret_field])
    for zone in zones:
        pop[:, zone_map[zone[0]]] = zone[1]*bool_skim[:, zone_map[zone[0]]]
        ret[:, zone_map[zone[0]]] = zone[3]*bool_skim[:, zone_map[zone[0]]]
        nre[:, zone_map[zone[0]]] = (zone[2] - zone[3])*bool_skim[:, zone_map[zone[0]]]

    #Calculate the row sums to get the total number of people, retail, and non-retail jobs that can be reached within a specific time for each origin zone
    acc_pop = pop.sum(1)
    acc_ret = ret.sum(1)
    acc_nre = nre.sum(1)

    #Update the shapefile with the calculated accessibilities
    zones = arcpy.da.UpdateCursor(taz_file, field_names = [taz_field, accpop_name, accret_name, accnre_name])
    for zone in zones:
        zone[1] = acc_pop[zone_map[zone[0]]]
        zone[2] = acc_ret[zone_map[zone[0]]]
        zone[3] = acc_nre[zone_map[zone[0]]]
        zones.updateRow(zone)

    #Unlock the shapefile
    del zone
    del zones

def calc_auto_att(bool_skim, zone_map, taz_file):
    '''
    Calculates the number of people, retail, and non-retail jobs that can reach each zone within a specific time. Attractivenesses in the input shapefile are updated.

    Parameters
    ----------
    bool_skim (ndarray):
        2-dimensional Boolean "skim"
    zone_map (dict):
        Dictionary mapping zone number to index in the skim
    taz_file (str):
        Filepath for a TAZ shapefile
    '''
    global taz_field, pop_field, emp_field, ret_field, attpop_name, attret_name, attnre_name

    pop = np.empty_like(bool_skim, dtype = int)
    ret = np.empty_like(bool_skim, dtype = int)
    nre = np.empty_like(bool_skim, dtype = int)

    #For each zone, create ndarrays that represent the number of people, retail, and non-retail jobs that can reach a zone within a specific time
    zones = arcpy.da.SearchCursor(taz_file, field_names = [taz_field, pop_field, emp_field, ret_field])
    for zone in zones:
        pop[zone_map[zone[0]], :] = zone[1]*bool_skim[zone_map[zone[0]], :]
        ret[zone_map[zone[0]], :] = zone[3]*bool_skim[zone_map[zone[0]], :]
        nre[zone_map[zone[0]], :] = (zone[2] - zone[3])*bool_skim[zone_map[zone[0]], :]

    #Calculate the column sums to get the total number of people, retail, and non-retail jobs that can reach each destination zone within a specific time
    att_pop = pop.sum(0)
    att_ret = ret.sum(0)
    att_nre = nre.sum(0)

    #Update the shapefile with the calculated attractivenesses
    zones = arcpy.da.UpdateCursor(taz_file, field_names = [taz_field, attpop_name, attret_name, attnre_name])
    for zone in zones:
        zone[1] = att_pop[zone_map[zone[0]]]
        zone[2] = att_ret[zone_map[zone[0]]]
        zone[3] = att_nre[zone_map[zone[0]]]
        zones.updateRow(zone)

    #Unlock the shapefile
    del zone
    del zones

def calc_transit_acc(bool_skim, zone_map, taz_file):
    '''
    Calculates the number of jobs that can be accessed by transit within a specified time for each zone. Accessibilities in the input shapefile are updated.

    Parameters
    ----------
    bool_skim (ndarray):
        2-dimensional Boolean "skim"
    zone_map (dict):
        Dictionary mapping zone number to index in the skim
    taz_file (str):
        Filepath for a TAZ shapefile
    '''
    global taz_field, emp_field, trnacc_name

    emp = np.empty_like(bool_skim, dtype = int)

    #Calculate number of jobs that can be reached by each origin zone in each destination zone within a specific time
    zones = arcpy.da.SearchCursor(taz_file, field_names = [taz_field, emp_field])
    for zone in zones:
        emp[:, zone_map[zone[0]]] = zone[1]*bool_skim[:, zone_map[zone[0]]]

    #Calculate the row sums to get the total number of jobs that each origin zone can reach within a specific time
    trn_acc = emp.sum(1)

    #Update the shapefile with the calculated accessbilities
    zones = arcpy.da.UpdateCursor(taz_file, field_names = [taz_field, trnacc_name])
    for zone in zones:
        zone[1] = trn_acc[zone_map[zone[0]]]
        zones.updateRow(zone)

    #Unlock the shapefiles
    del zone
    del zones


arcpy.AddMessage('Adding Fields if they are absent')
current_fields = [field.aliasName for field in arcpy.ListFields(taz_file)]
new_fields = [accpop_name, accret_name, accnre_name, attpop_name, attret_name, attnre_name, trnacc_name]
for field in new_fields:
    if field not in current_fields:
        try:
            arcpy.AddField_management(taz_file, field, 'LONG')
        except Exception:
            arcpy.AddMessage("Adding a new field didn't work")
            continue

arcpy.AddMessage('Reading in Auto Skim')
(auto, auto_zones) = extract_skim_from_csv(auto_skim_file)

arcpy.AddMessage('Creating auto Boolean "skim"')
auto_bool = create_auto_bool_skim(auto)

arcpy.AddMessage('Reading in Transit Skim')
(transit, transit_zones) = extract_skim_from_csv(transit_skim_file)

arcpy.AddMessage('Creating transit Boolean "skim"')
transit_bool = create_transit_bool_skim(transit)

arcpy.AddMessage('Calculating Auto Accessibility')
calc_auto_acc(auto_bool, auto_zones, taz_file)

arcpy.AddMessage('Calculating Auto Attractiveness')
calc_auto_att(auto_bool, auto_zones, taz_file)

arcpy.AddMessage('Calculting Transit Accessibility')
calc_transit_acc(transit_bool, transit_zones, taz_file)
