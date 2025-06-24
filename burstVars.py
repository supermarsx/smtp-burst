# Size constants
SZ_KILOBYTE = 1024
SZ_MEGABYTE = 1024 * SZ_KILOBYTE
SZ_GIGABYTE = 1024 * SZ_MEGABYTE
SZ_TERABYTE = 1024 * SZ_GIGABYTE

#SB_SGEMAILS		integer, Emails per segment
#SB_SGEMAILSPSEC	integer, Time between emails
#SB_BURSTS			integer, Number of email segment bursts
#SB_BURSTSPSEC		integer, Time between each burst
#SB_TOTAL			integer, Total emails, auto calculated
#SB_SIZE			integer, Size of random data to append to message
#SB_STOPFAIL		boolean, Stop when SB_STOPFQNT emails fail to send
#SB_STOPFQNT		integer, Number of failed emails to trigger a stop
#SB_FAILCOUNT		integer, Failed email counter
SB_SGEMAILS		= 5
SB_SGEMAILSPSEC	= 1
SB_BURSTS		= 3
SB_BURSTSPSEC	= 3
SB_TOTAL		= SB_SGEMAILS * SB_BURSTS
SB_SIZE			= 5 * SZ_MEGABYTE * 2
SB_STOPFAIL		= True
SB_STOPFQNT		= 3
SB_FAILCOUNT	= 0

#SB_SENDER		string, Sender email
#SB_RECEIVERS 	array,	Array of receiver emails
#SB_SERVER		string, SMTP server receiving emails
#SB_MESSAGEC	string, Message being sent
SB_SENDER		= 'from@sender.com'
SB_RECEIVERS 	= ['to@receiver.com']
SB_SERVER		= 'smtp.mail.com'
SB_MESSAGEC		= """From: SENDER <from@sender.com>
To: RECEIVER <to@receiver.com>
Subject: SUBJECT

MESSAGE DATA

"""
