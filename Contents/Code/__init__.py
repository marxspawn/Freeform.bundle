NAME = "Freeform"
PREFIX = '/video/freeform'
BASE_URL = "http://freeform.go.com"

ICON = 'icon-default.jpg'
ART = 'art-default.jpg'

SEASONS = "http://watchabcfamily.go.com/vp2/s/carousel?service=seasons&parser=VP2_Data_Parser_Seasons&showid=%s&view=season"
EPISODES = "http://watchabcfamily.go.com/vp2/s/carousel?service=playlists&parser=VP2_Data_Parser_Playlist&postprocess=VP2_Data_Carousel_ProcessPlaylist&showid=%s&seasonid=%s&vidtype=lf&view=showplaylist&playlistid=PL5515994&start=0&size=100&paging=1"
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
    oc.add(DirectoryObject(key=Callback(Shows, title='Featured Shows', section_id='1532518'), title='Featured Shows'))
    oc.add(DirectoryObject(key=Callback(Shows, title='Other Shows', section_id='1703286'), title='Other Shows'))

    return oc

####################################################################################################
@route(PREFIX + '/shows')
def Shows(title, section_id):

    oc = ObjectContainer()
    html = HTML.ElementFromURL(BASE_URL + '/shows')

    for item in html.xpath('//div[@class="modules"]//section[@data-m-id="%s"]//li' %section_id):

        url = item.xpath('./a/@href')[0]
        if '/movies-and-specials/' in url:
            continue
        title = url.split('/')[-1].replace('-', ' ').title()
        url = BASE_URL + url
        thumb = item.xpath('.//img/@src')[0]
        
        oc.add(DirectoryObject(
            key = Callback(Season, url=url, title=title, thumb=thumb),
            title = title,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no shows listed." )
    else:
        return oc

####################################################################################################
@route(PREFIX + '/season')
def Season(title, url, thumb):

    oc = ObjectContainer(title2=title)
    show_id = GetShowID(url)
    html = GetHTML(SEASONS % show_id)

    for season in html.xpath('//a'):

        title = season.text
        season_id = season.get('seasonid')

        if not season_id:
            season_id = title.rsplit(' ', 1)[1]

        oc.add(DirectoryObject(
            key = Callback(Episodes, title=title, show_id=show_id, season=season_id),
            title = title,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no seasons listed." )
    else:
        return oc

####################################################################################################
@route(PREFIX + '/episodes')
def Episodes(title, show_id, season):

    oc = ObjectContainer(title2=title)
    html = GetHTML(EPISODES % (show_id, season))

    for episode in html.xpath('//div[contains(@class, "reg_tile")]'):

        url = episode.xpath('.//a/@href')[0]

        title = episode.xpath('./div[@class="tile_title"]/a/text()')[0]
        duration = int(episode.xpath('./@duration')[0])
        try: summary = episode.xpath('./div[@class="tile_desc"]/text()')[0]
        except: summary = ''
        thumb = episode.xpath('./div[@class="thumb"]/a/img/@src')[0]
        air_date = episode.xpath('./div[@class="show_tile_sub"]/text()')[0].split('Aired ')[1]
        originally_available_at = Datetime.ParseDate(air_date).date()

        oc.add(VideoClipObject(
            url = '%s#%s' % (url, show_id),
            title = title,
            summary = summary,
            duration = duration,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb)
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no unlocked videos for this show." )
    else:
        return oc

####################################################################################################
def GetHTML(url):

    try: html = HTML.ElementFromURL(url, sleep=5.0)
    except: html = HTML.ElementFromURL(url, cacheTime=0)

    return html

####################################################################################################
@route(PREFIX + '/getshowid')
def GetShowID(url):

    try: content = HTTP.Request(url, cacheTime=CACHE_1DAY).content
    except: content = ''
    try: show_id = RE_SHOW_ID.search(content).group(1)
    except: show_id = ''

    return show_id
