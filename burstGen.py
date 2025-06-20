import random, smtplib
from smtplib import *
from burstVars import *

# Size constants
SZ_KILOBYTE = 1024
SZ_MEGABYTE = 1024 * SZ_KILOBYTE
SZ_GIGABYTE = 1024 * SZ_MEGABYTE
SZ_TERABYTE = 1024 * SZ_GIGABYTE

# Generate random data
# size 		integer, size in bytes
def genData(size):
	return bytearray(random.getrandbits(8) for i in range(size)).decode("utf-8", "ignore")

# Append message with generated data
def appendMessage() :
	return (SB_MESSAGEC + genData(SB_SIZE)).encode('ascii', 'ignore')

# Get human readable size from sizeof
# num 		integer, size in bytes
# suffix 	integer, suffix to append
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
	
# Send email
# number 		integer, 	Email number
# burst			integer, 	Burst round
# SB_FAILCOUNT 	integer, 	Current send fail count
# SB_MESSAGE	string, 	Message string to send
def sendmail(number, burst, SB_FAILCOUNT, SB_MESSAGE):
	if SB_FAILCOUNT.value >= SB_STOPFQNT && SB_STOPFAIL == True :
		pass

	print("%s/%s, Burst %s : Sending Email" % (number, SB_TOTAL, burst))
	try:
	   smtpObj = smtplib.SMTP(SB_SERVER)
	   smtpObj.sendmail(SB_SENDER, SB_RECEIVERS, SB_MESSAGE)         
	   print("%s/%s, Burst %s : Email Sent" % (number, SB_TOTAL, burst))
	except SMTPException:
		SB_FAILCOUNT.value += 1
		print("%s/%s, Burst %s/%s : Failure %s/%s, Unable to send email" % (number, SB_TOTAL, burst, SB_BURSTS, SB_FAILCOUNT.value, SB_STOPFQNT))
	except SMTPSenderRefused:
		SB_FAILCOUNT.value += 1
		print("%s/%s, Burst %s : Failure %s/%s, Sender refused" % (number, SB_TOTAL, burst, SB_BURSTS, SB_FAILCOUNT.value, SB_STOPFQNT))
	except SMTPRecipientsRefused:
		SB_FAILCOUNT.value += 1
		print("%s/%s, Burst %s : Failure %s/%s, Recipients refused" % (number, SB_TOTAL, burst, SB_BURSTS, SB_FAILCOUNT.value, SB_STOPFQNT))
	except SMTPDataError:
		SB_FAILCOUNT.value += 1
		print("%s/%s, Burst %s : Failure %s/%s, Data Error" % (number, SB_TOTAL, burst, SB_BURSTS, SB_FAILCOUNT.value, SB_STOPFQNT))
