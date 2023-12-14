"""
Author: Emanuel Ivanaj - Software Engineer
Date:   30/11/2023

Script that update a log file in a real-time way updating all the mission status every 3 seconds
"""

import threading
import time
import os
import glob
from os.path import join
from datetime import datetime

from ANTServerRESTClient import ANTServerRestClient
from ToolsAPI import ServerManager, VehicleManager

# Global variables
Nome_veicolo = "AGV"
Percorso_Cartella_Log = "Log"

# Get the latest file (today)
def get_latest_file(directory):
    list_of_files = glob.glob(os.path.join(directory, '*'))
    if not list_of_files:
        return None  # No files in the directory

    latest_file = max(list_of_files, key=os.path.getctime)
    return os.path.basename(latest_file)

#Extract all the ids from the log file
def extract_ids_from_log(log_file_path):
    ids = []

    try:
        with open(log_file_path, 'r') as log_file:
            for line in log_file:
                words = line.split()
                if 'ID:' in words:
                    id_index = words.index('ID:')
                    if id_index + 1 < len(words):
                        id_value = words[id_index + 1]
                        ids.append(id_value)

        return ids
    except Exception as e:
        pass

# Update the log file with the retrived data 
def update_log_file(log_file_path, results, messages, vehicle_alarms, vehicle_error):
    try:
        with open(log_file_path, 'r+') as log_file:
            lines = log_file.readlines()

            for log_id, values in results.items():
                for i, line in enumerate(lines):
                    if f'ID: {log_id}' in line:
                        arriving_time = values.get('arrivingtime', '')
                        formatted_date = format_arriving_time(arriving_time)

                        if is_mission_started(values):
                            update_started_mission(log_file, lines, i, formatted_date, values, messages, vehicle_alarms, vehicle_error)
                        else:
                            update_uncompleted_mission(log_file, lines, i, formatted_date, values, messages, vehicle_alarms, vehicle_error)

                        break

            log_file.seek(0)
            log_file.writelines(lines)
            log_file.truncate()

    except Exception as e:
        pass

#Get the data when the AGV is arrived
def format_arriving_time(arriving_time):
    if arriving_time:
        parsed_date = datetime.fromisoformat(arriving_time)
        return parsed_date.strftime("%d-%m-%Y %H:%M:%S")
    return ''

# The combination of these 3 parameters means that the AGV is running the mission
def is_mission_started(values):
    return (
        values["state"] == 2
        and values["navigationstate"] == 3
        and values["transportstate"] == 4
    )


def update_started_mission(log_file, lines, i, formatted_date, values, messages, vehicle_alarms, vehicle_error):
    # Aggiorna il file di log per una missione completata
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%d-%m-%Y')
    current_hour, current_minute, current_second = (
        current_datetime.hour,
        current_datetime.minute,
        current_datetime.second,
    )
    date_time = f"{current_date} {current_hour:02d}:{current_minute:02d}:{current_second:02d}"

    if not lines[i + 1].split(':', 1)[1].strip():
        lines[i + 1] = f' Mission launched at: {date_time}\n'

    lines[i + 2] = f' Finished at:         {formatted_date} |\n'
    lines[i + 3] = f' Error: {vehicle_error}\n'
    lines[i + 4] = f' Alarm: {vehicle_alarms}\n'
    lines[i + 7] = f' State: {values["state"]}\n'
    lines[i + 8] = f' Navigation state: {values["navigationstate"]}\n'
    lines[i + 9] = f' Transport state: {values["transportstate"]}\n'
    lines[i + 10] = f' Messages: {messages}\n'

def update_uncompleted_mission(log_file, lines, i, formatted_date, values, messages, vehicle_alarms, vehicle_error):
    # Aggiorna il file di log per una missione non completata
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%d-%m-%Y')
    current_hour, current_minute, current_second = (
        current_datetime.hour,
        current_datetime.minute,
        current_datetime.second,
    )
    date_time = f"{current_date} {current_hour:02d}:{current_minute:02d}:{current_second:02d}"
    #Write the new values inside respective lines
    missione_lanciata = lines[i + 1].split(':', 1)[1].strip()
    if missione_lanciata and values["transportstate"] == 8:
        missione_lanciata2 = lines[i + 2].split('|', 1)[1].strip()
        if missione_lanciata2 == 'Time difference: N/A':
            data1 = datetime.strptime(date_time, "%d-%m-%Y %H:%M:%S")
            data2 = datetime.strptime(str(missione_lanciata), "%d-%m-%Y %H:%M:%S")
            diff = data1 - data2
            lines[i + 2] = f' Finished at:         {formatted_date} | Time difference: {diff}\n'
            lines[i + 3] = f' Error: {vehicle_error}\n'
            lines[i + 4] = f' Alarm: {vehicle_alarms}\n'
            lines[i + 7] = f' State: {values["state"]}\n'
            lines[i + 8] = f' Navigation state: {values["navigationstate"]}\n'
            lines[i + 9] = f' Transport state: {values["transportstate"]}\n'
            lines[i + 10] = f' Messages: {messages}\n'
    else:
        lines[i + 2] = f' Finished at:         {formatted_date} | Time difference: N/A\n'
        lines[i + 3] = f' Error: {vehicle_error}\n'
        lines[i + 4] = f' Alarm: {vehicle_alarms}\n'
        lines[i + 7] = f' State: {values["state"]}\n'
        lines[i + 8] = f' Navigation state: {values["navigationstate"]}\n'
        lines[i + 9] = f' Transport state: {values["transportstate"]}\n'
        lines[i + 10] = f' Messages: {messages}\n'

#Check the state from the ANT-SERVER
def check_state(vehicle_state, log_file_path, messages, vehicle_alarms, vehicle_error):
    if len(vehicle_state) >= 22:
        vehicle_state = vehicle_state[:22]
    # Update the log file only if the vehicle state has these 3 flags
    if vehicle_state in ["runningAMission", "MovingToChargerParking", "inError"]:
        ant_client = ANTServerRestClient()
        server_manager = ServerManager(ant_client)
        #Retrive the last 120 missions. This number is calculated on a per-customer worst-case basis
        list_mission2 = server_manager.get_missions_info(120)
        file = get_latest_file(log_file_path)
        file_path = join(log_file_path, file)
        ids = extract_ids_from_log(file_path)

        results = {}
        for log_id in ids:
            for mission in list_mission2:
                if mission['missionid'] == log_id:
                    results[log_id] = {
                        'state': mission['state'],
                        'navigationstate': mission['navigationstate'],
                        'transportstate': mission['transportstate'],
                        'arrivingtime': mission['arrivingtime'] if 'arrivingtime' in mission and mission['arrivingtime'] != "" else '',
                    }
                    break

        update_log_file(file_path, results, messages, vehicle_alarms, vehicle_error)

def thread_function():
    global Nome_veicolo
    global Percorso_Cartella_Log

    while True:
        ant_client = ANTServerRestClient()
        vehicle_manager = VehicleManager(ant_client)
        vehicle_json = vehicle_manager.get_vehicle_info(Nome_veicolo)
        messages = vehicle_json.get('state', {}).get('messages', [])
        #Retrive the data from JSON answer
        try:
            vehicle_state = vehicle_json['state']['vehicle.state'][0]
        except:
            vehicle_state = ""

        try:
            vehicle_alarms = vehicle_json['alarms'][0]
        except:
            vehicle_alarms = ""

        try:
            vehicle_error = vehicle_json['state']['errors'][0]
        except:
            vehicle_error = ""

        check_state(vehicle_state, Percorso_Cartella_Log, messages, vehicle_alarms, vehicle_error)
        time.sleep(3)

# Create the thread
thread = threading.Thread(target=thread_function)
thread.start()
