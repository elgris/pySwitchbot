# Findings:
- The API corrects time from the current "true time" (000000 sets the time to my current timezone).
Perhaps the starting point is the "firmware time" that you could get with other commands that it sends before.
- 57:0f:68:05:06 is the command code, perhaps used for both requesting and setting the time.
- code 80 - minus to the current time, code 00 - plus
- it uses all 3 bytes.
Need a script that calcualtes 
b1b1-b2b2: b1b1 * 4 - minutes ...
0f00: 20:35 -> 19:31 (1235 -> 1171, diff: 64)
ff00: 20:36 -> 2:28 (1236 -> 148, diff: 1088)
1000: 20:40 -> 19:32 (1240 -> 1172, diff: 68)
f000: 21:56 -> 4:52 (1316 -> 292, diff: 1024)
1000: 22:06 -> 20:57 (1326 -> 1257, diff: 69), 22:08 -> 21:00 (1328 -> 1260, diff: 68)
Next steps:
- turn the device off and see how setting the "zero" changes it after being offline for a while.
    RESULT: oddly enough, the time didn't change at all.

Communication log:
"570f690506": 01-80-00-00-00
"570f6901":  01-e4-00-97-2b-00-07-e9-0c-1d-15-2f-01
"570f68050680000000": 01

01-e4- 02- 94- 23- 00- 07- e9- 0c- 1e -08-37-01
ok-mfr-mfr-mfr-mfr-mfr-???-???-mm-dd-hh-mm-ss

01-e4-00-97-2b-00-07-e9-0c-1d-15-2f-01
01-e4-00-97-2b-00-07-e9-0c-1d-15-30-01
01-e4-00-97-2b-00-07-e9-0c-1d-15-30-25
21:53: 01-e4-00-97-29-00-07-e9-0c-1d-15-35-00
22:04: 01-e4-09-96-29-00-07-e9-0c-1d-16-04-00
22:28: 01-e4-08-96-28-00-07-e9-0c-1d-16-1c-01
08:46: 01-e4-07-93-2b-00-07-e9-0c-1e-08-2e-01
08:47: 01-e4-09-93-22-00-07-e9-0c-1e-08-2f-00
08:53: 01-e4-01-94-23-00-07-e9-0c-1e-08-35-01
08:54: 01-e4-01-94-23-00-07-e9-0c-1e-08-36-01
08:55: 01-e4-02-94-23-00-07-e9-0c-1e-08-37-01

08:47: 01-> e4-09-93-22-00< -07-e9-0c-1e-08-2f-00
mfr: b0-e9-fe-e9-68-ad-11-> e4-09-93-22-00 <-08-02-c3-00

21:56 -> 4:52
22:06 -> 20:57
I suspect that the request should contain time delta from some internal timestamp that the device somehow stores. Examples: 
- request payload "57:0f:68:05:06:80:00:00:00" sets the time on the device to the current time. 
- request payload "57:0f:68:05:06:80:00:01:00" sets the time on the device to the current time minus 4 minutes.
- request payload "57:0f:68:05:06:00:00:01:00" sets the time on the device to the current time plus 4 minutes.
- request payload "57:0f:68:05:06:80:00:0f:00" sets the time on the device to the current time minus 64 minutes.  
- request payload "57:0f:68:05:06:80:00:f0:00" sets the time on the device to the current time minus 1024 minutes.  

Can you guess the format of the request payload using this new data?

01-00 - can it be 256 seconds?
3600 - 0e10

# Results
Yes, the last 3 bytes encode the number of seconds, offset from the currently stored timestamp. Wonder how the watch sets arbitrary time and date then.

The watch doesn't allow setting the date though. Only time +-23hrs 59mins (which doesn't fit in 2 bytes, that's why you need 3 bytes).


# Decoding response of get time command "570f6901"
It returns time as displayed, timezone and delta included.
The format is as following  :
ok-mfr-mfr-mfr-mfr-12/24-???-???-mm-dd-hh-mm-ss?
01-e4- 02- 94- 23- 00- 07- e9- 0c- 1e -08-37-01

12/24 - time display format, 80 - for 12h, 00 - for 24h

mfr data also comes in a handshake. Contains temperature.
Example: mfr: b0-e9-fe-e9-68-ad-11-> e4-09-93-22 <-00-08-02-c3-00


01-e4-07-96-25-80-07-e9-0c-13-0a-34-01
10:53pm
Includes the adjust delta

# Decoding "adjust time" command "570f680506..."
57:0f:68:05:06:80:00:f0:00
___req_code___:+-:seconds
+-: 80 - minus seconds from the current time, 00 - plus seconds

## A command with no arguments, just "570f680506" yields the following response:
Returns the current "adjust time" offset
01-80-0f-10-00
ok:+-:seconds

# Decoding set time command "57000503" (?)
57:00:05:03:0d:00:00:00:00:69:52:91:10:00
__req_code_:tz:??:??:??:??:_timestamp_:add
- tz: 0c - UTC, 00 - UTC-12, then it can go up indefinitely.
- add - tells how many minutes were added to the timestamp to represent a "partial" timezone (e.g. UTC+5,5, here you'll see 1e - 30 minutes). For such timezones:
 - the tz value contains the truncated integer part.
 - timestamp contains extra minutes from the partial part.
 - the extra minutes are reported in `add`.  
- this command doesn't contain 12h/24h mode, it is set by another command
- Partial UTC (e.g for India UTC+5:30) - apparently the thing uses integer timezone (UTC+5) and adds 30 minutes to the timestamp.
Questions:

# Decoding set time format (12/24) command: "570f680505"
- 570f68050580 - 12h format
- 570f68050500 - 24h format

# Implementation idea:
- send 570f6901 periodically. If it gets different from the local time - update the local time. Do not update it constantly.
## Settings time:
- adjust time, set the offset to 0.
- set time.

# Idea
Write a blog post and how you used your gpt as a rubber duck. And how it responded utterly uselessly. Maybe try the same conversation with Gemini?


# Next steps
- Intercept the traffic from the beginning again and check if the phone sends new time / timezone / date.
- factory reset the watch to see what time it shows by default.