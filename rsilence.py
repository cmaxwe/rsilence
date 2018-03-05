# Silence skip
# Requires:
#  - Python 2.7
#  - ffmpeg
#  - argparse (pip install argparse)
import argparse
import subprocess
import re, os, time
from datetime import date, datetime, timedelta


# Print output with a timestamp
def tprint(outString):
	outString = datetime.now().strftime('%m/%d/%y %H:%M:%S - ') + outString
	print(outString) 


# Takes an input filename and an output filename and skips the silence
def silenceSkip(input, output, cutOnly):
	tprint("Analyzing " + input + " for silence.")
	command = "ffmpeg -y -nostats -i " + input + " -max_muxing_queue_size 204800 -af silencedetect=n=-50dB:d=10 -c:v copy -c:a ac3 -f mp4 /dev/null"
	p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	pi = iter(p.stdout.readline, b'')
	marks = []
	marks.append('0')
	for line in pi:
		if('silencedetect' in line):
			start_match = re.search(r'.*silence_start: (.*)',line, re.M|re.I)
			end_match = re.search(r'.*silence_end: (.*) \|.*',line, re.M|re.I)
			if(start_match != None and start_match.lastindex == 1):
				marks.append(start_match.group(1))
				#tprint("Start: " + start_match.group(1))
			if(end_match != None and end_match.lastindex == 1):
				marks.append(end_match.group(1))
				#tprint("End: " + end_match.group(1))
	# If it is not an even number of segments then add the end point. If the last silence goes
	# to the endpoint then it will be an even number.
	if(len(marks)%2 == 1):
		marks.append('end')

	# Make a temp dir
	command = 'mkdir ./temp'
	subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).wait()

	tprint("Creating segments.")
	seg = 0
	# Create segments
	for i in range(0,len(marks)):
		if(i%2==0):
			if(marks[i+1] != 'end'):
				seg = seg + 1
				length = float(marks[i+1]) - float(marks[i])
				command = 'ffmpeg -y -nostats -i ' + input + ' -ss ' + str(float(marks[i])+0.5) + ' -t ' + str(float(length)-0.5) + ' -c:v copy -c:a copy -bsf:a aac_adtstoasc ./temp/cut' + str(seg) + '.mp4'
			else:
				seg = seg + 1
				command = 'ffmpeg -y -nostats -i ' + input + ' -ss ' + str(marks[i]) + ' -c:v copy -c:a copy -bsf:a aac_adtstoasc ./temp/cut' + str(seg) + '.mp4'
			subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).wait()

	if(not cutOnly):
		# Create file list
		file = open("./temp/concat_list.txt", "w")
		for i in range(1,seg+1):
			# If it is a valid video then add it to the list
			location = 'cut' + str(i) + '.mp4'
			file.write("file\t" + 'cut' + str(i) + '.mp4\n')
		file.close()

		command = 'ffmpeg -y -nostats -f concat -i ./temp/concat_list.txt -c copy ' + output
		subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).wait()
		tprint("Merging segments back to single video and saving: " + output)

		# Erase temp
		command = 'rm -rf ./temp'
		subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)



############## The body of the program ###################
parser = argparse.ArgumentParser(description='Takes a file and outputs a copy of the file with the silent parts removed.')
parser.add_argument('inArg', metavar='input', type=str, help='The input file.')
parser.add_argument('outArg', metavar='output', type=str, help='The output file.')
parser.add_argument('-cutOnly', dest='cutOnly', action='store_true', help='Creates the pieces in the temp directory but does not stitch them tegether.')

args = parser.parse_args()
silenceSkip(args.inArg, args.outArg, args.cutOnly)
