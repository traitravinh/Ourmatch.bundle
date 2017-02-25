import urllib
import urllib2
import re
from BeautifulSoup import BeautifulSoup

NAME = "Ourmatch"
BASE_URL = "http://ourmatch.net"
playwire_base_url='http://cdn.playwire.com/'
default_ico = 'icon-default.png'
##### REGEX #####
RE_MENU = Regex('<div class="division">(.+?)<div class="ads_mid">')
RE_INDEX = Regex('<div id="main-content">(.+?)<footer id="footer">')
RE_PAGE = Regex('<div class="loop-nav pag-nav">(.+?)<footer id="footer">')
RE_IFRAME = Regex('<div id="main-content">(.+?)</div><!-- end #content -->')
RE_PUBID = Regex('data-publisher-id="(.+?)" data-video-id')
RE_VIDID = Regex('data-video-id="(.+?)"')
RE_SRC = Regex('"src":"(.+?)"|\'')
RE_VCODE = Regex('mp4:(.+?)" ')
RE_DAILY = Regex('src="(.+?)"')
# ###################################################################################################

def Start():
    ObjectContainer.title1 = NAME
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:22.0) Gecko/20100101 Firefox/22.0'
    HTTP.Headers['X-Requested-With'] = 'XMLHttpRequest'


####################################################################################################
@handler('/video/ourmatch', NAME)
def MainMenu():
    oc = ObjectContainer()
    try:
        link = HTTP.Request(BASE_URL,cacheTime=3600).content
        newlink = ''.join(link.splitlines()).replace('\t','')
        match = RE_MENU.search(newlink).group(1)
        li = BeautifulSoup(str(match.replace('\t','')))('li',{'class':'hover-tg'})

        oc.add(DirectoryObject(
            key=Callback(Category, title='Latest Games', catelink=BASE_URL),
            title='Latest Games',
            thumb=R(default_ico)
        ))

        for l in li:
            lilink = BeautifulSoup(str(l))('a')[0]['href']
            lititle = BeautifulSoup(str(l))('a')[0].contents[0]
            oc.add(DirectoryObject(
                key=Callback(Category, title=lititle, catelink=lilink),
                title=lititle,
                thumb=R(default_ico)
            ))

    except Exception, ex:
        Log("******** Error retrieving and processing latest version information. Exception is:\n" + str(ex))

    return oc


####################################################################################################
@route('/video/ourmatch/category')
def Category(title, catelink):
    oc = ObjectContainer(title2=title)
    link = HTTP.Request(catelink,cacheTime=3600).content
    newlink = ''.join(link.splitlines()).replace('\t','')
    match = RE_INDEX.search(newlink).group(1)
    thumbtag = BeautifulSoup(str(match))('div',{'class':'thumb'})
    for t in thumbtag:
        tlink = BeautifulSoup(str(t))('a')[0]['href']
        ttitle = BeautifulSoup(str(t))('a')[0]['title']
        timage = BeautifulSoup(str(t))('img')[0]['src']
        oc.add(DirectoryObject(
                key=Callback(Episodes, title=ttitle, eplink=tlink, epthumb=timage),
                title=ttitle,
                thumb=timage
        ))

    match_pages = RE_PAGE.search(newlink).group(1)
    wp_pagenavi = BeautifulSoup(str(match_pages))('div',{'class':'wp-pagenavi'})
    page_larger = BeautifulSoup(str(wp_pagenavi[0]))('a')
    for p in page_larger:
        plink = BeautifulSoup(str(p))('a')[0]['href']
        ptitle = BeautifulSoup(str(p))('a')[0].contents[0]
        oc.add(DirectoryObject(
                key=Callback(Category, title=ptitle, catelink=plink),
                title=ptitle,
                thumb=R(default_ico)
        ))

    return oc

####################################################################################################
@route('/video/ourmatch/episodes')
def Episodes(title, eplink, epthumb):
    oc = ObjectContainer(title2=title)
    link = HTTP.Request(eplink,cacheTime=3600).content

    newlink = ''.join(link.splitlines()).replace('\t','')
    vlink = retrievVideoLink(newlink)
    ptext = 'Highlights'
    oc.add(createMediaObject(
        url=vlink,
        title=ptext,
        thumb=epthumb,
        rating_key=ptext
    ))
    return oc

@route('/video/ourmatch/createMediaObject')
def createMediaObject(url, title,thumb,rating_key,include_container=False,includeRelatedCount=None,includeRelated=None,includeExtras=None):

    Log('<<PLAY VIDEO>> - '+title)
    Log('<<VIDEO LINK>> - '+url)

    container = Container.MP4
    video_codec = VideoCodec.H264
    audio_codec = AudioCodec.AAC
    audio_channels = 2
    track_object = EpisodeObject(
        key = Callback(
            createMediaObject,
            url=url,
            title=title,
            thumb=thumb,
            rating_key=rating_key,
            include_container=True
        ),
        title = title,
        thumb=thumb,
        rating_key=rating_key,
        items = [
            MediaObject(
                parts=[
                    PartObject(key=Callback(PlayVideo, url=url))
                ],
                container = container,
                video_codec = video_codec,
                audio_codec = audio_codec,
                audio_channels = audio_channels,
                optimized_for_streaming = True
            )
        ]
    )

    if include_container:
        return ObjectContainer(objects=[track_object])
    else:
        return track_object


@indirect
def PlayVideo(url):
    return IndirectResponse(VideoClipObject, key=url)

def retrievVideoLink(url):
    sources = re.compile('<source src="(.+?)"></video>').findall(url)
    finallink = sources[0]
    return finallink


####################################################################################################
