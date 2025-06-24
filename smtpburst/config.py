# Size constants
SZ_KILOBYTE = 1024
SZ_MEGABYTE = 1024 * SZ_KILOBYTE
SZ_GIGABYTE = 1024 * SZ_MEGABYTE
SZ_TERABYTE = 1024 * SZ_GIGABYTE

# Default runtime parameters
SB_SGEMAILS = 5
SB_SGEMAILSPSEC = 1
SB_BURSTS = 3
SB_BURSTSPSEC = 3
SB_TOTAL = SB_SGEMAILS * SB_BURSTS
SB_SIZE = 5 * SZ_MEGABYTE * 2
SB_STOPFAIL = True
SB_STOPFQNT = 3
SB_FAILCOUNT = 0

SB_SENDER = 'from@sender.com'
SB_RECEIVERS = ['to@receiver.com']
SB_SERVER = 'smtp.mail.com'
SB_MESSAGEC = """From: SENDER <from@sender.com>
To: RECEIVER <to@receiver.com>
Subject: SUBJECT

MESSAGE DATA

"""

# Proxy and authentication defaults
SB_PROXIES = []
SB_USERLIST = []
SB_PASSLIST = []
