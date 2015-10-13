This project contains server code which runs on a raspberry PI, monitors the condition of GPIO for triggers and sends a message through Google Cloud Message (GCM) to the matching Android app SAHomeMonitor.

License: Apache 2.0
Contains code from Python-GCM licensed under the MIT License (see GCM-README.md)

Usage:

Run the samonitorserver module from the command line with a single parameter containing the GCM API Key obtained from Google (see http://developer.android.com/guide/google/gcm/gcm.html).

An optional relay server can be setup to relay the GCM messages from a different server.  See the documentation in the gcmrelay modules for more information.  The value use_gcm_relay in the samonitorserver determines whether the relay server is used.

For the doorbell, the wave file to be played is stored in /etc/samonitor/doorbell.wav