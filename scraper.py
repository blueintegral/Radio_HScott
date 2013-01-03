#!/usr/bin/env python
from subprocess import call
import urllib2
from bs4 import BeautifulSoup
import os
import json
import requests
import hmac
from md5 import md5
import hashlib
import re
#Grooveshark API credentials:
GSKey = 'radio_hscott'
GSSecret = 'grooveshark API key here	'
TSSecret = 'TinySong API key here' 
GSPlaylist = '78886427'

def getPeakSongs():
	print "Getting Peak Songs..."
	#os.system('rm now-playing.html')
	#First, grab a copy of the list. Need to fake the user agent, otherwise we'll get an HTTP 403. 
	#wget'ing the page doesn't work, we need to do a proper GET
	opener = urllib2.build_opener(urllib2.HTTPHandler)
	req = urllib2.Request('http://www.thepeak.fm/modules/mod_nowplaying/ajaxreceiver.php?d=0&s=00:00&e=23:45')
	req.add_header('User-agent','Mozilla/5.0')
	result = urllib2.urlopen(req)
	response = result.read()
	#print response

	#Now use Beautiful Soup to get song data
	soup = BeautifulSoup(response)
	dat = [map(str, row.findAll("td")) for row in soup.findAll("tr") ]
	#print dat

	#Parse all that data to get an array of songs 
	#Delete the first element. Then loop through the array and read 2 elements, submit them to tinysong, add the returned link to a playlist, then delete the next 2 elements in the array, and loop.
	dat.pop(0)
	artists = []
	songs = []
	for i in dat:
		#dat is a list of lists, so we need to remove the first element, since that has time, which we don't care about
	#	print i
		i.pop(0)
		artist = i.pop(0)
		song = i.pop(0)
		artist = artist[24:]
		song = song[23:]
		artist = artist[:-5] #Remove the </td> from the end of the artist and song
		song = song[:-5]
		artist = artist.replace('&amp;', '&')
		song = song.replace('&amp;', '&')
		artists.append(artist)
		songs.append(song)

	#print artists
	#print songs
	return (songs, artists)

def savePeakSongs():
	print "Saving today's songs..."
	songJson = open("songs.json", "r+")
	readSong = songJson.read()
	jsondata = json.loads(readSong)
	songs, artists = getPeakSongs()
	print len(songs)
	print len(jsondata)
	for x in range(len(songs)):
		songitem = {}
		songitem['name'] = songs[x]
		songitem['artist'] = artists[x]
		songitem['songquery'] = songitem['name'].replace(' ','+') + '+' + songitem['artist'].replace(' ','+')
		jsondata.append(songitem)
	songJson.seek(0)
	songJson.write(json.dumps(jsondata, indent=4))
	songJson.close()

def cleanPeakSongs():
	print "Cleaning the songs for dupes..."
	fullList = open("songs.json", "r")
	readList = fullList.read()
	fullJson = json.loads(readList)
	cleanList = [dict(t) for t in set([tuple(d.items()) for d in fullJson])]
	cleanJson = open("cleansongs.json", "r+")
	cleanJsonRead = cleanJson.read()
	if cleanJsonRead:
		cleanJsonLoaded = json.loads(cleanJsonRead)
		cleanList[0]['currentID'] = len(cleanJsonLoaded)
	else:
		cleanList[0]['currentID'] = 1249
	cleanJson.seek(0)
	cleanJson.write(json.dumps(cleanList, indent=4))
	cleanJson.close()
	fullList.close()

def getSongIDS():
	print "Getting Song IDs..."
	songlist = open("cleansongs.json", "r")
	readsongs = songlist.read()
	songjson = json.loads(readsongs)
	tinysongs = open("tinysongs.json", "r+")
	tinyjson = tinysongs.read()
	jsondata = json.loads(tinyjson)
	newID = songjson[0]['currentID']
	lastID = len(songjson)
	songnum = 0
	print "Already have " + str(songjson[0]['currentID']) + " songs!"
	print "Total: " + str(len(songjson))
	for x in range(newID, lastID): # len(songs) to handle all
		song = songjson[x]
		print str(songnum) + ": " + song['name'] + " by " + song['artist']
		songnum += 1
		songitem = {}
		songitem['name'] = song['name']
		songitem['artist'] = song['artist']
		queryurl = 'http://tinysong.com/b/' + song['songquery'] + '?format=json&key=' + TSSecret
		r = requests.get(queryurl)
		tinyresponse = r.json
		if tinyresponse:
			if "SongID" in tinyresponse.keys():
				songitem['SongID'] = tinyresponse['SongID']
			else:
				songitem['SongID'] = False
				print "No SongID"
		else:
			print "No response :("
			songitem['SongID'] = False
		jsondata.append(songitem)
	tinysongs.seek(0)
	tinysongs.write(json.dumps(jsondata, indent=4))
	tinysongs.close()
	songlist.close()

def makeSongList():
	print "Making a list of songs..."
	tinysongs = open("tinysongs.json", "r")
	tinyjson = tinysongs.read()
	jsondata = json.loads(tinyjson)
	songlist = open("songlist.json", "w")
	finalList = []
	for song in jsondata:
		if song['SongID']:
			finalList.append(song['SongID'])
	songlist.write(json.dumps(finalList, indent=4))
	songlist.close()

def loadAndSetPlaylist():
	print "About to send the songs to GrooveShark..."
	songlist = open("songlist.json", "r")
	songjson = songlist.read()
	fullsonglist = json.loads(songjson)
	status = setPlaylistSongs(fullsonglist)
	if status == 1:
		print "It Worked!"
	else:
		print "Try again :("

# Call official Grooveshark api.

def setPlaylistSongs(songlist):
	print "Sending songs to GrooveShark..."
	sessionData = '{"method":"setPlaylistSongs","header":{"wsKey":"radio_hscott","sessionID":"' + sessionID + '"},"parameters":{"playlistID":"' + GSPlaylist + '","songIDs":' + json.dumps(songlist) + '}}'
	groovyURL = createSig(sessionData)
	r = requests.post(groovyURL, data=sessionData)
	successStatus = json.loads(r.text)['result']['success']
	return successStatus

def callGrooveShark():
	jsonfile = open("songs.json", "r")
	jsonstr = jsonfile.read()
	jsondata = json.loads(jsonstr)
	# print jsondata

	for song in jsondata:
		if song['SongID']:
		#	gsurl = GSAPI + song['SongID'] + 
			gsrequest = urllib2.Request(gsurl)
			gsresult = urllib2.urlopen(gsrequest)
			gsresponse = json.loads(gsresult.read())

def createSig(params):
	myhmac = hmac.new(GSSecret, params).hexdigest()
	groovyURL = 'https://api.grooveshark.com/ws/3.0/?sig=' + myhmac
	return groovyURL

def startSession():
	sessionData = '{"method":"startSession","header":{"wsKey":"radio_hscott"},"parameters":[]}'
	groovyURL = createSig(sessionData)
	#print groovyURL
	#print sessionData
	r = requests.post(groovyURL, data=sessionData)
	#print r.url
	#print r.text
	sessionID = json.loads(r.text)['result']['sessionID']
	#print sessionID
	return sessionID

def loginUser():
	sessionData = '{"method":"authenticate","header":{"wsKey":"radio_hscott","sessionID":"'+ sessionID +'"},"parameters":{"login":"aloishis89","password":"e669b244aae2f082b8ba3f885a3a3991"}}'
	groovyURL = createSig(sessionData)
	r = requests.post(groovyURL, data=sessionData)
	#print (json.loads(r.text)['result']['success'])
	if not(json.loads(r.text)['result']['success']):
		print 'Error: Could not successfully log in'
	else: 
		print 'Logged in!'

# Every day, download the most recent day of music by Peak
savePeakSongs()
# Clean the new songs for duplicates with the older list.
cleanPeakSongs()
# Query tinysongs when necessary to get new song IDS.
getSongIDS()
# Make a list of songs for the playlist
makeSongList()
# Start a new session with the Grooveshark API
sessionID = startSession()
#Now we need to log in a user (me) so we can create a playlist
loginUser()
# Send GS the updated playlist.
loadAndSetPlaylist()