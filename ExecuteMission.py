"""
Author: Emanuel Ivanaj - Software Engineer
Date: 23/11/2023
"""

from os.path import dirname, join
import os
import sys
import json
import time
import psutil
from ANTServerRESTClient import MissionType, RetCode, ANTServerRestClient
from ToolsAPI import MissionMaker
from ToolsAPI import ServerManager
from datetime import datetime, timedelta
from ToolsAPI import VehicleManager
import subprocess
import shlex

def main(Pick, Drop):
    """
    Check if the parameters, throught terminal, are OK
    """
    if len(sys.argv) < 3 or len(sys.argv) > 3:
        print("Execute mission")
        print("Usage : python ExecuteMission.py Pick_Name Drop_Name")
        return None

	################################################################
    # Path where the folder will be placed
    log_folder = 'Log'

    # Vehicle name
    vehicleName = 'AGV'

    # After 30 days the script will delete older files
    giorni_per_cancellare_file_log = 30
	################################################################

    # Check if the folder already exist
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # Delete the files older then 30 days
    delete_old_log_files(log_folder, giorni_per_cancellare_file_log)

    # Creation of the objects used to iterate
    ant_client = ANTServerRestClient()
    mission_maker = MissionMaker(ant_client)

    # Launch a mission 
    res = launch_mission(mission_maker, Pick, Drop)

    # Check the error if the mission was not launched correctly
    if res["retcode"] is not RetCode.NO_ERROR.value:
        print("Error while creating the mission")
        print("\n\nIng. E.Ivanaj")
        return
    else:
        server_manager = ServerManager(ant_client)
        vehicle_manager = VehicleManager(ant_client)

        # Retrive the infos about the last launched mission
        mission_info = get_latest_mission_info(server_manager)

        # Variable used for the log file
        fromNode = Pick
        toNode = Drop

        # add the data to the log file
        log_file_path = create_log_file(log_folder, fromNode, toNode, res, mission_info, vehicleName, vehicle_manager)

        # Retrive added infos
        list_mission2 = server_manager.get_missions_info(120)
        IDs = ids = extract_ids_from_log(log_file_path)

        # Create a dictionary to save the data
        results = get_results_dict(IDs, list_mission2)

        # Update the log file with the new mission data
        update_log_file(log_file_path, results)

        # Execute the batch log file in a new window
        batch_file_path = 'script.bat'
        console_window_title = "Robopac log thread (Ing. Emanuel Ivanaj)"
        
        # Check if the batch script is already in execution or already exists
        if not is_batch_running(console_window_title):
            subprocess.Popen(['start', 'cmd', '/k', f'title {console_window_title} && {batch_file_path}'], shell=True)
            print("Batch file executed.")

        print("\nMission successfully created with ID:", res['payload']['acceptedmissions'][0])
        print("\n\nIng. E.Ivanaj\n\n")

        return res['payload']['acceptedmissions'][0]

def launch_mission(mission_maker, Pick, Drop):
    """
    Launch the mission
    """
    return mission_maker.create_mission(MissionType.NODE_TO_NODE, Pick, Drop, "Default Payload")

def get_latest_mission_info(server_manager):
    """
    Retrieve the data from the last mission
    """
    list_mission = server_manager.get_missions_info(1)
    return list_mission[0]

def extract_ids_from_log(log_file_path):
    """
    Extract all the ids from the log file
    """
    # Initialize an empty list where i will save the ids
    ids = []

    # Open the log file and read line by line
    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            # Split the line into words
            words = line.split()

            # Check if the line contains the word "ID:"
            if 'ID:' in words:
                # Find the word ID
                id_index = words.index('ID:')

                # The value of ID is extracted after ":"
                if id_index + 1 < len(words):
                    id_value = words[id_index + 1]
                    ids.append(id_value)

    return ids

def is_batch_running(console_window_title):

    try:
        current_pid = os.getpid()
        for process in psutil.process_iter(['pid', 'name', 'create_time', 'cmdline']):
            if process.pid == current_pid:
                # Ignore the actual process
                continue
            # Check if the project is already launched
            if process.info['name'] == 'cmd.exe' and process.info['cmdline'] is not None and console_window_title in ' '.join(map(str, process.info['cmdline'])):
                
                return True
    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
        # Actually is not important for me to manage exceptions. Here you can add whatever you want
        pass

    # If the cycle does not found an active process it will return False
    return False
	
def update_log_file(log_file_path, results):
    """
    Update the log file with retrived infos
    """

    # Open the file in write and read mode
    with open(log_file_path, 'r+') as log_file:
        # Read all the lines 
        lines = log_file.readlines()

        # Find and replace the data inside the log file
        for log_id, values in results.items():
            # Find the ID
            for i, line in enumerate(lines):
                if f'ID: {log_id}' in line:
                    arriving_time = values.get('arrivingtime', '')
                    if arriving_time:
                        parsed_date = datetime.fromisoformat(arriving_time)
                        formatted_date = parsed_date.strftime("%d-%m-%Y %H:%M:%S")
                    else:
                        formatted_date = ''

                    #lines[i + 2] = f' Finished at: {formatted_date} |\n'
                    lines[i + 7] = f' State: {values["state"]}\n'
                    lines[i + 8] = f' Navigation state: {values["navigationstate"]}\n'
                    lines[i + 9] = f' Transport state: {values["transportstate"]}\n'
                    break

        # I will position at the top of the log file
        log_file.seek(0)

        # Write all the modified lines 
        log_file.writelines(lines)

        # Truncate the file to remove any remaining data
        log_file.truncate()

def create_log_file(log_folder, fromNode, toNode, res, mission_info, vehicleName, vehicle_manager):
    """
    Create the log file and add the initial data
    """
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%d-%m-%Y')
    current_hour = current_datetime.hour
    current_minute = current_datetime.minute
    current_second = current_datetime.second
    dateTime = str(current_date)+' '+ str(current_hour)+':'+str(current_minute)+':'+str(current_second)
    accepted_missions_str = str(res['payload']['acceptedmissions'][0])
    log_file_path = os.path.join(log_folder, ''+str(current_date)+'.txt')

    if not os.path.exists(log_file_path):
        with open(log_file_path, "w") as file:
            pass

    vehicleJSON = vehicle_manager.get_vehicle_info(vehicleName)
    errors_value = vehicleJSON.get('state', {}).get('errors', [])
    batteryInfo = str(vehicleJSON['state']['battery.info'][0])
    alarms_value = vehicleJSON.get('alarms', [])
    vehicle_state_list = vehicleJSON['state']['vehicle.state']
    extracted_value = vehicle_state_list[0]

    with open(log_file_path, 'r') as log_file:
        current_content = log_file.read()

    with open(log_file_path, 'w') as log_file:
        log_file.write(' From Node: {} \n To Node: {} \n ID: {} \n Mission launched at: \n Finished at: {} | \n Error: {} \n Alarm: {} \n Battery: {}% \n Vehicle state: {}\n State: {}\n Navigation state: {}\n Transport state: {}\n Messages: \n-----------------------------------------------------------------------------------------------------------------------------\n\n'.format(
            fromNode, toNode, accepted_missions_str, dateTime, ', '.join(map(str, errors_value)), ', '.join(map(str, alarms_value)), batteryInfo, extracted_value, mission_info['state'], mission_info['navigationstate'], mission_info['transportstate']
        ))
        log_file.write(current_content)

    return log_file_path

def delete_old_log_files(log_folder, giorni_per_cancellare_file_log):
    """
    Delete all the files that are older then a specific parameter
    """
    # Obtaining the actual date
    current_date = datetime.now()

    # Calculate: Actual date - 30 days
    thirty_days_ago = current_date - timedelta(days=giorni_per_cancellare_file_log)

    # Check all the files inside the log folder
    for file_name in os.listdir(log_folder):
        file_path = os.path.join(log_folder, file_name)

        if os.path.isfile(file_path):
            try:
                # Extract the first 10 chars of the file name in order to compare the dates
                file_date = datetime.strptime(file_name[:10], '%d-%m-%Y')

                # Check if the date is older then 30 days 
                if file_date < thirty_days_ago:
                    # Delete the file
                    os.remove(file_path)
                    print(f"Deleted old log file: {file_name}")
            except ValueError:
                # Ignore the fils with invalid names
                pass

def get_results_dict(IDs, list_mission2):
    """
    Create a dictionary with the mission results
    """
    results = {}
    for log_id in IDs:
        for mission in list_mission2:
            if mission['missionid'] == log_id:
                if 'arrivingtime' in mission and mission['arrivingtime'] != "":
                    results[log_id] = {
                        'state': mission['state'],
                        'navigationstate': mission['navigationstate'],
                        'transportstate': mission['transportstate'],
                        'arrivingtime': mission['arrivingtime']
                    }
                else:
                    results[log_id] = {
                        'state': mission['state'],
                        'navigationstate': mission['navigationstate'],
                        'transportstate': mission['transportstate']
                    }
                break
    return results

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
