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
    try:
        if str(url).find('data-publisher-id')!=-1:
            publisherId = re.compile('data-publisher-id="(.+?)" data-video-id').findall(url)
            videoId = re.compile('data-video-id="(.+?)"').findall(url)

            f4m_link = playwire_base_url+'v2/' + str(publisherId[0])+'/config/'+str(videoId[0])+'.json'
            link = urllib2.urlopen(f4m_link).read()
            f4m_src = re.compile('"src":"(.+?)"|\'').findall(str(link))
            if str(f4m_src[0]).find('.f4m')!=-1:
                nlink = urllib2.urlopen(f4m_src[0]).read()
                vCode = re.compile('mp4:(.+?)" ').findall(str(nlink))
                if len(vCode)>1:
                    sCode = vCode[1]
                else:
                    sCode=vCode[0]
                real_link = playwire_base_url+publisherId[0]+'/'+str(sCode)
            elif str(f4m_src[0]).find('rtmp://streaming')!=-1:
                real_link = str(f4m_src[0]).replace('rtmp://streaming','http://cdn').replace('mp4:','')

            return real_link
        else:
            if url.find('player.json')!=-1:
                manifest_link = re.compile('data-config="(.+?)"').findall(url)[0].replace('player.json','manifest.f4m')
            else:
                manifest_link = re.compile('data-config="(.+?)"').findall(url)[0].replace('zeus.json','manifest.f4m')
            hosting_id = re.compile('//config.playwire.com/(.+?)/videos').findall(url)[0]
            if manifest_link.find('http:')==-1:
                manifest_link= 'http:'+manifest_link
            link = urllib2.urlopen(manifest_link).read()
            newlink = ''.join(link.splitlines()).replace('\t','')
            base_url = re.compile('<baseURL>(.+?)</baseURL>').findall(newlink)[0]
            if newlink.find('video-hd.mp4?hosting_id=')!=-1:
                media_id = '/video-hd.mp4?hosting_id='+hosting_id
            else:
                media_id='/video-sd.mp4?hosting_id='+hosting_id
            real_link = base_url+media_id
            return real_link
    except:pass


####################################################################################################
