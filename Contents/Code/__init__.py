import ssl, urllib2

NAME = 'Freeform'
ART = 'art-default.jpg'
ICON = 'icon-default.jpg'

ALL_SHOWS = 'https://api.mobile.aws.abcf.seabc.go.com/api/search-index.json'
SHOW_EPISODES = 'https://api.mobile.aws.abcf.seabc.go.com/api/shows/%s'

HTTP_HEADERS = {
	'User-Agent': 'ABCFamily/4.2.1 (iPad; iOS 10.2.1; Scale/2.00)'
}

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.ClearCache()

####################################################################################################
@handler('/video/freeform', NAME, art=ART, thumb=ICON)
def MainMenu():

	oc = ObjectContainer()
	json_obj = JSON.ObjectFromString(GetData(ALL_SHOWS))

	for show in json_obj['shows']:

		episodes_available = False

		# Check for at least one free episode available in any season before adding a show to the list
		for season in show['seasons']:
			for episode in season['episodes']:

				if episode['accesslevel'] == '0':
					episodes_available = True
					break

			if episodes_available:
				break

		if not episodes_available:
			continue

		show_title = show['name']
		summary = show['description']
		thumb = show['thumbnail']['v1x']
		id = show['api_endpoint'].split('/')[-1]

		oc.add(DirectoryObject(
			key = Callback(Season, show_title=show_title, thumb=thumb, id=id),
			title = show_title,
			summary = summary,
			thumb = thumb
		))

	return oc

####################################################################################################
@route('/video/freeform/season')
def Season(show_title, thumb, id):

	oc = ObjectContainer(title2=show_title)
	json_obj = JSON.ObjectFromString(GetData(SHOW_EPISODES % (id)))

	# Check for at least one free episode available in a season before adding the season to the list
	for season in json_obj['seasons']:

		episodes_available = False

		for episode in season['episodes']:

			if episode['accesslevel'] == '0':
				episodes_available = True
				break

		if not episodes_available:
			continue

		season_num = season['num']
		title = 'Season %s' % (season_num)

		oc.add(DirectoryObject(
			key = Callback(Episodes, show_title=show_title, title=title, id=id, season_num=season_num),
			title = title,
			thumb = thumb
		))

	return oc

####################################################################################################
@route('/video/freeform/episodes')
def Episodes(show_title, title, id, season_num):

	oc = ObjectContainer(title2=title)
	json_obj = JSON.ObjectFromString(GetData(SHOW_EPISODES % (id)))

	for season in json_obj['seasons']:

		if season['num'] != season_num:
			continue

		for episode in season['episodes']:

			if episode['accesslevel'] != '0':
				continue

			oc.add(EpisodeObject(
				url = 'freeform://%s' % (episode['partner_api_id']),
				show = show_title,
				title = episode['name'],
				summary = episode['description'],
				index = int(episode['num']),
				season = int(episode['season_num']),
				duration = int(float(episode['duration']) * 1000),
				originally_available_at = Datetime.ParseDate(episode['airdate'].split('T')[0]).date(),
				thumb = Resource.ContentsOfURLWithFallback(url=episode['thumbnail']['v1x'])
			))

	return oc

####################################################################################################
@route('/video/abc/getdata')
def GetData(url):

	# Quick and dirty workaround to get this to work on Windows
	# Do not validate ssl certificate
	# http://stackoverflow.com/questions/27835619/ssl-certificate-verify-failed-error
	if 'Windows' in Platform.OS:
		req = urllib2.Request(url, headers=HTTP_HEADERS)
		ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
		data = urllib2.urlopen(req, context=ssl_context).read()
	else:
		data = HTTP.Request(url, headers=HTTP_HEADERS).content

	return data
