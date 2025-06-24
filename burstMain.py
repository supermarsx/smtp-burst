import time
import sys
from multiprocessing import Process, Manager

from burstVars import *
from burstGen import *

# Main script routine
if __name__ == '__main__':

	print("Starting smtp-burst")
	manager = Manager()
	SB_FAILCOUNT = manager.Value('i', 0)
	
	print("Generating %s of data to append to message" % (sizeof_fmt(SB_SIZE)))
	SB_MESSAGE = appendMessage()
	print("Message using %s of random data" % (sizeof_fmt(sys.getsizeof(SB_MESSAGE))))
	
	print("Sending %s messages from %s to %s through %s" % (SB_TOTAL, SB_SENDER, SB_RECEIVERS, SB_SERVER))
	
	for x in range(0, SB_BURSTS):
		quantity = range(1, SB_SGEMAILS + 1)
		procs = []
		

		if SB_FAILCOUNT.value >= SB_STOPFQNT and SB_STOPFAIL == True :
			break
		for index, number in enumerate(quantity):
			if SB_FAILCOUNT.value >= SB_STOPFQNT and SB_STOPFAIL == True :
				break
			time.sleep(SB_SGEMAILSPSEC)
			process = Process(target=sendmail, args=(number + (x * SB_SGEMAILS), x + 1, SB_FAILCOUNT, SB_MESSAGE))
			procs.append(process)
			process.start()
			
	 
		for process in procs:
			process.join()
		time.sleep(SB_BURSTSPSEC)