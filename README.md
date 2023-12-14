#AGV
Python script to run the Bluebotics AGV.
This project is executed via terminal and it is necessary to pass the parameters to be able to launch the mission, example:

ExecuteMission.py Pick Drop

The example I wrote was written using the command line.
If the ANT-SERVER is active and the Pick name and Drop name are written correctly, the mission will be sent to the ANT-SERVER
The script also works with a log file, which is why it will create a new process to continuously update the log file in real time.

Note: install psutil and json using these commands: pip install psutil and pip install json

Log file example:

 From Node: Pick_2 
 To Node: Drop 
 ID: 3651 
 Mission launched at: 14-12-2023 11:59:22
 Finished at:         14-12-2023 12:00:07 | Time difference: 0:00:46
 Error: 
 Alarm: 
 Battery: 90% 
 Vehicle state: runningAMission
 State: 2
 Navigation state: 4
 Transport state: 8
 Messages: []
---------------------------------------------------------------------------------

 From Node: Pick_2 
 To Node: Drop 
 ID: 3650 
 Mission launched at: 14-12-2023 11:54:45
 Finished at:         14-12-2023 11:55:28 | Time difference: 0:00:44
 Error: 
 Alarm: 
 Battery: 90% 
 Vehicle state: runningAMission
 State: 2
 Navigation state: 4
 Transport state: 8
 Messages: []
---------------------------------------------------------------------------------
