#AGV
Python script to run the Bluebotics AGV.
This project is executed via terminal and it is necessary to pass the parameters to be able to launch the mission, example:

ExecuteMission.py Pick Drop

The example I wrote was written using the command line.
If the ANT-SERVER is active and the Pick name and Drop name are written correctly, the mission will be sent to the ANT-SERVER
The script also works with a log file, which is why it will create a new process to continuously update the log file in real time.

Note: install psutil and json using these commands: pip install psutil and pip install json
