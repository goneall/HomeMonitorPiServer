This project contains server code which runs on a raspberry PI, 
monitors the condition of GPIO for triggers and sends 
messages to HomeAssistant and Pushover.

License: Apache 2.0

Usage:

Run the samonitorserver module from the command line with the following parameters:

- Pushover App token
- Pushover user key
- HomeAssistant URL (optional)


An optional relay server can be setup to relay the GCM messages from a different server.  See the documentation in the gcmrelay modules for more information.  The value use_gcm_relay in the samonitorserver determines whether the relay server is used.

For the doorbell, the wave file to be played is stored in /etc/samonitor/doorbell.wav