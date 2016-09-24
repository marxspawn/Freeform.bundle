NAME = "Freeform"
PREFIX = '/video/freeform'
BASE_URL = "http://freeform.go.com"

ICON = 'icon-default.jpg'
ART = 'art-default.jpg'

VIDEOS = 'http://api.contents.watchabc.go.com/vp2/ws/s/contents/3000/videos/002/001/-1/%s/-1/-1/-1/-1.json'
RE_SHOW_ID = Regex('/(SH\d+)')

####################################################################################################
def Start():

    ObjectContainer.title1 = NAME
    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON)
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'

####################################################################################################
@handler(PREFIX, NAME, thumb=ICON, art=ART)
def MainMenu():

    oc = ObjectContainer()
    html = HTML.ElementFromURL(BASE_URL + '/shows')

    for item in html.xpath('//section[contains(@data-m-name,"tilegroup")]'):

        section_id = item.xpath('./@id')[0]
        title = section_id.replace('-', ' ').title()
        
        oc.add(DirectoryObject(
            key = Callback(Shows, section_id=section_id, title=title),
            title = title
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no shows listed." )
    else:
        return oc

####################################################################################################
@route(PREFIX + '/shows')
def Shows(title, section_id):

    oc = ObjectContainer()
    html = HTML.ElementFromURL(BASE_URL + '/shows')

    #for item in html.xpath('//div[@class="modules"]//section[@data-m-id="%s"]//li' %section_id):
    for item in html.xpath('//div[@class="modules"]//section[@id="%s"]//li' %section_id):

        url = item.xpath('./a/@href')[0]
        if '/movies-and-specials/' in url:
            continue
        title = url.split('/')[-1].replace('-', ' ').title()
        url = BASE_URL + url
        thumb = item.xpath('.//img/@src')[0]
        
        oc.add(DirectoryObject(
            key = Callback(Episodes, url=url, title=title),
            title = title,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no shows listed." )
    else:
        return oc

####################################################################################################
@route(PREFIX + '/newepisodes')
def Episodes(url, title):

    oc = ObjectContainer(title2=title)
    show_id = GetShowID(url)
    json = JSON.ObjectFromURL(VIDEOS % (show_id))

    for episode in json['video']:

        if 'accesslevel' in episode and episode['accesslevel'] != "0":
            continue

        oc.add(EpisodeObject(
            url = episode['url'],
            title = episode['title'],
            summary = episode['longdescription'],
            index = int(episode['episodenumber']),
            season = int(episode['season']['num']),
            duration = int(episode['duration']['value']),
            originally_available_at = Datetime.ParseDate(episode['airdates']['airdate'][0]).date(),
            thumb = Resource.ContentsOfURLWithFallback(url=episode['thumbnails']['thumbnail'][0]['value'])
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no unlocked videos for this show." )
    else:
        return oc

####################################################################################################
@route(PREFIX + '/getshowid')
def GetShowID(url):

    try: content = HTTP.Request(url, cacheTime=CACHE_1DAY).content
    except: content = ''
    try: show_id = RE_SHOW_ID.search(content).group(1)
    except: show_id = ''

    return show_id
