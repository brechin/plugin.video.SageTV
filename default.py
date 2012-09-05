import urllib,urllib2,re
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
import os
import simplejson as json
import unicodedata
import time
from xml.dom.minidom import parse
from time import strftime
from datetime import date

__settings__ = xbmcaddon.Addon(id='plugin.video.SageTV')
__language__ = __settings__.getLocalizedString
__cwd__      = __settings__.getAddonInfo('path')

# SageTV recording Directories for path replacement
sage_rec = __settings__.getSetting("sage_rec")
sage_unc = __settings__.getSetting("sage_unc")

# SageTV URL based on user settings
strUrl = 'http://' + __settings__.getSetting("sage_user") + ':' + __settings__.getSetting("sage_pass") + '@' + __settings__.getSetting("sage_ip") + ':' + __settings__.getSetting("sage_port")
iconImage = xbmc.translatePath(os.path.join(__cwd__,'resources','media','icon.png'))
DEFAULT_CHARSET = 'utf-8'

def TOPLEVELCATEGORIES():
 
	#addTopLevelDir('[Watch Recordings]', strUrl + '/',1,iconImage,'Browse previously recorded and currently recording shows')
	#addTopLevelDir('[Watch Recordings]', strUrl + '/sagex/api?command=EvaluateExpression&1=GetMediaFiles("T")&encoder=json',1,iconImage,'Browse previously recorded and currently recording shows')
	#addTopLevelDir('[Watch Recordings]', strUrl + '/sagex/api?command=EvaluateExpression&1=GroupByMethod(GetMediaFiles("T"),"GetMediaTitle")&encoder=json',1,iconImage,'Browse previously recorded and currently recording shows')
	addTopLevelDir('[Watch Recordings]', strUrl + '/sagex/api?command=EvaluateExpression&1=Sort(java_util_Map_keySet(GroupByMethod(GetMediaFiles("T"),"GetMediaTitle")),false,"Natural")&encoder=json',1,iconImage,'Browse previously recorded and currently recording shows')
	addTopLevelDir('[View Upcoming Recordings]', strUrl + '/sagex/api?command=GetScheduledRecordings&encoder=json',2,iconImage,'View and manage your upcoming recording schedule')
	
def WATCHRECORDINGS(url,name):
	#Get the list of Recorded shows
	addDir('[All Shows]',url,11,iconImage,'')
	titleObjects = executeSagexAPIJSONCall(strUrl + '/sagex/api?command=EvaluateExpression&1=GroupByMethod(GetMediaFiles("T"),"GetMediaTitle")&encoder=json', "Result")
	titles = titleObjects.keys()
	for title in titles:
		mfsForTitle = titleObjects.get(title)
		for mf in mfsForTitle:
			airing = mf.get("Airing")
			show = airing.get("Show")
			strTitle = airing.get("AiringTitle")
			strMediaFileId = str(mf.get("MediaFileID"))
			strExternalId = str(show.get("ShowExternalID"))
			#strTitle = strTitle.replace('&amp;','&')
			#strTitle = strTitle.replace('&quot;','"')
			#strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
			break
		urlToShowEpisodes = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByMethod(GetMediaFiles("T"),"GetMediaTitle","' + urllib2.quote(strTitle.encode("utf8")) + '",true)&encoder=json'
		#urlToShowEpisodes = strUrl + '/sage/Search?searchType=TVFiles&SearchString=' + urllib2.quote(strTitle.encode("utf8")) + '&DVD=on&sort2=airdate_asc&partials=both&TimeRange=0&pagelen=100&sort1=title_asc&filename=&Video=on&search_fields=title&xml=yes'
		print "ADDING strTitle=" + strTitle + "; urlToShowEpisodes=" + urlToShowEpisodes
		imageUrl = strUrl + "/sagex/media/poster/" + strMediaFileId
		#print "ADDING imageUrl=" + imageUrl
		addDir(strTitle, urlToShowEpisodes,11,imageUrl,strExternalId)

def VIDEOLINKS(url,name):
	mfs = executeSagexAPIJSONCall(url, "Result")
	print "# of EPISODES for " + name + "=" + str(len(mfs))
	if(mfs == None or len(mfs) == 0):
		print "NO EPISODES FOUND FOR SHOW=" + name
		xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=True)
		return

	for mf in mfs:
		airing = mf.get("Airing")
		show = airing.get("Show")
		strMediaFileID = str(mf.get("MediaFileID"))
		strTitle = airing.get("AiringTitle")
		strEpisode = show.get("ShowEpisode")
		if(strEpisode == None):
			strEpisode = ""		
		strDescription = show.get("ShowDescription")
		if(strDescription == None):
			strDescription = ""		
		strGenre = show.get("ShowCategoriesString")
		strAiringID = str(airing.get("AiringID"))
		seasonNum = int(show.get("ShowSeasonNumber"))
		episodeNum = int(show.get("ShowEpisodeNumber"))
		
		startTime = float(airing.get("AiringStartTime") // 1000)
		strAiringdateObject = date.fromtimestamp(startTime)
		airTime = strftime('%H:%M', time.localtime(startTime))
		strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
		strOriginalAirdate = strAiringdate
		if(airing.get("OriginalAiringDate")):
			startTime = float(airing.get("OriginalAiringDate") // 1000)
			strOriginalAirdateObject = date.fromtimestamp(startTime)
			strOriginalAirdate = "%02d.%02d.%s" % (strOriginalAirdateObject.day, strOriginalAirdateObject.month, strOriginalAirdateObject.year)

		# if there is no episode name use the description in the title
		if(strEpisode == ""):
			strDisplayText = strTitle + ' - ' + strDescription
		# else if there is an episode use that
		else:
			strDisplayText = strTitle + ' - ' + strEpisode
		strFilepath = mf.get("SegmentFiles")[0]
		
		imageUrl = strUrl + "/sagex/media/poster/" + strMediaFileID
		addMediafileLink(strDisplayText,strFilepath.replace(sage_rec, sage_unc),strDescription,imageUrl,strGenre,strOriginalAirdate,strAiringdate,strTitle,strMediaFileID,strAiringID,seasonNum,episodeNum)

def VIEWUPCOMINGRECORDINGS(url,name):
	#req = urllib.urlopen(url)
	airings = executeSagexAPIJSONCall(url, "Result")
	for airing in airings:
		show = airing.get("Show")
		strTitle = airing.get("AiringTitle")
		strEpisode = show.get("ShowEpisode")
		if(strEpisode == None):
			strEpisode = ""		
		strDescription = show.get("ShowDescription")
		if(strDescription == None):
			strDescription = ""		
		strGenre = show.get("ShowCategoriesString")
		strAiringID = str(airing.get("AiringID"))
		seasonNum = int(show.get("ShowSeasonNumber"))
		episodeNum = int(show.get("ShowEpisodeNumber"))
		
		startTime = float(airing.get("AiringStartTime") // 1000)
		strAiringdateObject = date.fromtimestamp(startTime)
		airTime = strftime('%H:%M', time.localtime(startTime))
		strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
		strOriginalAirdate = strAiringdate
		if(airing.get("OriginalAiringDate")):
			startTime = float(airing.get("OriginalAiringDate") // 1000)
			strOriginalAirdateObject = date.fromtimestamp(startTime)
			strOriginalAirdate = "%02d.%02d.%s" % (strOriginalAirdateObject.day, strOriginalAirdateObject.month, strOriginalAirdateObject.year)

		# if there is no episode name use the description in the title
		if(strEpisode == "" and strDescription == ""):
			strDisplayText = strTitle
		elif(strEpisode == ""):
			strDisplayText = strTitle + ' - ' + strDescription
		# else if there is an episode use that
		else:
			strDisplayText = strTitle + ' - ' + strEpisode
		strDisplayText = strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime + ": " + strDisplayText
		addAiringLink(strDisplayText,'',strDescription,iconImage,strGenre,strOriginalAirdate,strAiringdate,strTitle,strAiringID,seasonNum,episodeNum)

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

def addMediafileLink(name,url,plot,iconimage,genre,originalairingdate,airingdate,showtitle,mediafileid,airingid,seasonnum,episodenum):
        ok=True
        liz=xbmcgui.ListItem(name)
        scriptToRun = "special://home/addons/plugin.video.SageTV/contextmenuactions.py"
        actionDelete = "delete|" + strUrl + '/sagex/api?command=DeleteFile&1=mediafile:' + mediafileid
        actionCancelRecording = "cancelrecording|" + strUrl + '/sagex/api?command=CancelRecord&1=mediafile:' + mediafileid
        actionRemoveFavorite = "removefavorite|" + strUrl + '/sagex/api?command=EvaluateExpression&1=RemoveFavorite(GetFavoriteForAiring(GetAiringForID(' + airingid + ')))'
        bisAiringRecording = isAiringRecording(airingid)
        bisFavorite = isFavorite(airingid)
        if(bisAiringRecording == "true"):
          if(bisFavorite == "true"):
            liz.addContextMenuItems([('Delete Show', 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')'), ('Cancel Recording', 'XBMC.RunScript(' + scriptToRun + ', ' + actionCancelRecording + ')'), ('Remove Favorite', 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')')], True)
          else:
            liz.addContextMenuItems([('Delete Show', 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')'), ('Cancel Recording', 'XBMC.RunScript(' + scriptToRun + ', ' + actionCancelRecording + ')')], True)
        else:
          if(bisFavorite == "true"):
            liz.addContextMenuItems([('Delete Show', 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')'), ('Remove Favorite', 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')')], True)
          liz.addContextMenuItems([('Delete Show', 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')')], True)

        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot, "Genre": genre, "date": airingdate, "premiered": originalairingdate, "aired": originalairingdate, "TVShowTitle": showtitle, "season": seasonnum, "episode": episodenum } )
        liz.setIconImage(iconimage)
        liz.setThumbnailImage(iconimage)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
        return ok

def addAiringLink(name,url,plot,iconimage,genre,originalairingdate,airingdate,showtitle,airingid,seasonnum,episodenum):
	ok=True
	liz=xbmcgui.ListItem(name)
	scriptToRun = "special://home/addons/plugin.video.SageTV/contextmenuactions.py"
	#actionCancelRecording = "cancelrecording|" + strUrl + '/sagex/api?command=CancelRecord&1=mediafile:' + mediafileid
	actionRemoveFavorite = "removefavorite|" + strUrl + '/sagex/api?command=EvaluateExpression&1=RemoveFavorite(GetFavoriteForAiring(GetAiringForID(' + airingid + ')))'
	bisFavorite = isFavorite(airingid)
	if(bisFavorite == "true"):
		liz.addContextMenuItems([('Remove Favorite', 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')')], True)
	print "originalairingdate=" + originalairingdate + ";airingdate=" + airingdate
	liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot, "Genre": genre, "date": airingdate, "premiered": originalairingdate, "aired": originalairingdate, "TVShowTitle": showtitle, "season": seasonnum, "episode": episodenum } )
	liz.setIconImage(iconimage)
	liz.setThumbnailImage(iconimage)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
	return ok

# Checks if an airing is currently recording
def isAiringRecording(airingid):
	sageApiUrl = strUrl + '/sagex/api?command=IsFileCurrentlyRecording&1=airing:' + airingid
	return executeSagexAPICall(sageApiUrl, "Result")
		
# Checks if an airing has a favorite set up for it
def isFavorite(airingid):
	sageApiUrl = strUrl + '/sagex/api?command=IsFavorite&1=airing:' + airingid
	return executeSagexAPICall(sageApiUrl, "Result")
		
# Checks if an airing has a favorite set up for it
def getShowSeriesDescription(showexternalid):
	sageApiUrl = strUrl + '/sagex/api?command=EvaluateExpression&1=GetSeriesDescription(GetShowSeriesInfo(GetShowForExternalID("' + showexternalid + '")))'
	return executeSagexAPICall(sageApiUrl, "Result")
		
def executeSagexAPICall(url, resultToGet):
	#Log.Debug('*** sagex request URL: %s' % url)
	try:
		print "CALLING sageApiUrl=" + url
		input = urllib.urlopen(url)
	except IOError, i:
		print "ERROR in executeSagexAPICall: Unable to connect to SageTV server"
		return None

	content = parse(input)
	result = content.getElementsByTagName(resultToGet)[0].toxml()
	result = result.replace("<" + resultToGet + ">","")
	result = result.replace("</" + resultToGet + ">","")
	result = result.replace("<![CDATA[","")
	result = result.replace("]]>","")
	result = result.replace("<Result/>","")
	return result

def executeSagexAPIJSONCall(url, resultToGet):
	print "*** sagex request URL:" + url
	try:
		input = urllib.urlopen(url)
	except IOError, i:
		print "ERROR in executeSagexAPIJSONCall: Unable to connect to SageTV server"
		return None
	fileData = input.read()
	resp = unicodeToStr(json.JSONDecoder().decode(fileData))

	objKeys = resp.keys()
	numKeys = len(objKeys)
	if(numKeys == 1):
		return resp.get(resultToGet)
	else:
		return None

def addTopLevelDir(name,url,mode,iconimage,dirdescription):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name)

	liz.setInfo(type="video", infoLabels={ "Title": name, "Plot": dirdescription } )
	liz.setIconImage(iconimage)
	liz.setThumbnailImage(iconimage)
	#liz.setIconImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
	#liz.setThumbnailImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok

def addDir(name,url,mode,iconimage,showexternalid):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name)
	strSeriesDescription = ""
	strSeriesDescription = getShowSeriesDescription(showexternalid)

	liz.setInfo(type="video", infoLabels={ "Title": name, "Plot": strSeriesDescription } )
	liz.setIconImage(iconimage)
	liz.setThumbnailImage(iconimage)
	#liz.setIconImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
	#liz.setThumbnailImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok


def unicodeToStr(obj):
	t = obj
	if(t is unicode):
		return obj.encode(DEFAULT_CHARSET)
	elif(t is list):
		for i in range(0, len(obj)):
			obj[i] = unicodeToStr(obj[i])
		return obj
	elif(t is dict):
		for k in obj.keys():
			v = obj[k]
			del obj[k]
			obj[k.encode(DEFAULT_CHARSET)] = unicodeToStr(v)
		return obj
	else:
		return obj # leave numbers and booleans alone

	
params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

if mode==None or url==None or len(url)<1:
        print ""
        TOPLEVELCATEGORIES()
       
elif mode==1:
        print ""+url
        WATCHRECORDINGS(url,name)
        
elif mode==11:
        print ""+url
        VIDEOLINKS(url,name)
        
elif mode==2:
        print ""+url
        VIEWUPCOMINGRECORDINGS(url,name)

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)
xbmcplugin.setContent(int(sys.argv[1]),'episodes')
xbmcplugin.endOfDirectory(int(sys.argv[1]))