import urllib
import urllib2
import re
from BeautifulSoup import BeautifulSoup

NAME = "Ourmatch"
BASE_URL = "http://ourmatch.net"
playwire_base_url='http://cdn.playwire.com/'
default_ico = 'icon-default.png'
##### REGEX #####
RE_MENU = Regex('<div class="division">(.+?)<div id="ad-right">')
RE_INDEX = Regex('<div id="main-content">(.+?)<footer id="footer">')
RE_PAGE = Regex('<div class="loop-nav pag-nav">(.+?)<footer id="footer">')
RE_IFRAME = Regex('<div id="main-content">(.+?)<iframe src=')
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
    match = RE_IFRAME.search(newlink).group(1)
    p_tag = BeautifulSoup(str(match))('p')

    for p in p_tag:
        ptext = BeautifulSoup(str(p)).p.contents[0]
        plink = BeautifulSoup(str(p)).p.next.next.next
        Log(str(plink).find('dailymotion'))

        if str(plink).find('dailymotion')!=-1:
            plink = 'http:'+re.findall(RE_DAILY,str(plink))[0]
            oc.add(VideoClipObject(
                url=plink,
                title=ptext,
                thumb=epthumb
            ))
        else:
            pscritp =retrievVideoLink(str(plink))

            oc.add(createMediaObject(
                url=pscritp,
                title=ptext,
                thumb=epthumb,
                rating_key=ptext
            ))

    return oc

@route('/video/ourmatch/createMediaObject')
def createMediaObject(url, title,thumb,rating_key,include_container=False):
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
                video_resolution = '720',
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
    try:
        publisherId = RE_PUBID.search(url).group(1)
        videoId = RE_VIDID.search(url).group(1)
        f4m_link = playwire_base_url+'v2/' + str(publisherId)+'/config/'+str(videoId)+'.json'
        link = urllib2.urlopen(f4m_link).read()
        f4m_src = RE_SRC.search(link).group(1)

        if str(f4m_src).find('.f4m')!=-1:
            nlink = urllib2.urlopen(f4m_src).read()
            Log(nlink)
            vCode = re.findall(RE_VCODE,nlink)

            if len(vCode)>1:
                sCode = vCode[1]
            else:
                sCode=vCode[0]
            real_link = playwire_base_url+publisherId+'/'+str(sCode)
        elif str(f4m_src).find('rtmp://streaming')!=-1:
            real_link = str(f4m_src).replace('rtmp://streaming','http://cdn').replace('mp4:','')

        return real_link
    except:pass


####################################################################################################
