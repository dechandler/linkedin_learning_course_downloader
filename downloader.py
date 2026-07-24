import os
import re
import requests
import html
from bs4 import BeautifulSoup

############################# TO CHANGE START #############################

res = "720" # video resolution - 360, 540, 720, 1080. Check available options on the video player.
base_path = "/courses" # path to download courses - Windows example: c:/courses or c:\\courses
course_url = 'https://www.linkedin.com/learning/web-servers-and-apis-using-c-plus-plus/why-use-c-plus-plus-to-make-a-website' # any link from the course will do
skip = False # skip if video already exists

# https://cookie-script.com/documentation/how-to-check-cookies-on-chrome-and-firefox
jsession = 'ajax:6778916039974719485' # get value on 'jsession' cookie
li_at = 'AQEDAURmNjAE5Y0nAAABiNrKtugAAAGI_tc66E0ADgeMKZ55Ok3qpLsNUnCh-G8rkg60xjfDnzjTUCpyyrP7JGgxfA9BNKc00T-3UKMh2fzRJLR37FfFBupIPuVhKxyefuXDoC8dlCAp59QTSJl8ikSh' # get value on 'li_at' cookie

# IMPORTANT >>> Bear in mind that you need a premium Linkedin Learning subscription to download all videos.

############################# TO CHANGE END #############################

def clean_dir(course_name):
	course = course_name.lower().replace("c#", "c-sharp").replace(".net", "-dot-net")
	without_chars = re.sub(r'[\':)(,>.’/]', " ", course.strip()).replace("«", " ").replace("-»", " ").replace("»", " ").strip()
	return re.sub(r'(\s+)', "-", without_chars).replace("--", "-")

s = requests.Session()

ef_fn, ef_url = '', ''
slug = course_url.split('learning/')[1].split('/')[0]
base = 'https://www.linkedin.com/learning'
ctitle = slug.replace('-', ' ').title()
u = f'{base}/{slug}'

if not os.path.exists(base_path):
	os.makedirs(base_path)

h = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
	'Accept-Language': 'en-US,pt;q=0.5',
	'Accept-Encoding': '',
	'DNT': '1',
	'Connection': 'keep-alive',
	'Cookie': f'JSESSIONID={jsession}; lang=v=2&lang=en-US; li_at={li_at}',
	'Upgrade-Insecure-Requests': '1',
	'Sec-Fetch-Dest': 'document',
	'Sec-Fetch-Mode': 'navigate',
	'Sec-Fetch-Site': 'none',
	'Sec-Fetch-User': '?1',
	'TE': 'trailers',
}
# guest session to parse course sections and items, can be optionally changed
h_guest = h.copy()
h_guest['Cookie'] = 'JSESSIONID=ajax:0380846659549484462; lang=v=2&lang=en-us; bcookie="v=2&36413d99-45c4-4d33-8081-903c6c70c454"; bscookie="v=1&20230620225047fc09470c-d8b4-4032-84b9-780e238141b8AQGNv6BcipeTDDXc7fG1sv2NZzwMJVcX"; lidc="b=VGST02:s=V:r=V:a=V:p=V:g=2929:u=1:x=1:i=1687301447:t=1687387847:v=2:sig=AQHlFhttEakxKCATEP0ASa2rRozYocke"; li_alerts=e30=; li_gc=MTs0MjsxNjg3MzAxNTQ2OzI7MDIx8hmaDt4aTQe9qx4F8py0Bn8xz/5613aAmTHRpXmfsZk='



def get_video_metadata(course_slug, video_slug, headers):

    video_info_url = ''.join([
        "https://www.linkedin.com/learning-api/graphql",
        "?variables=(",
            "courseSlug:", course_slug, ",",
            "videoSlug:", video_slug,
        ")",
        "&queryId=videos.eb0cecfaa25dcd83d23769c32e492c1e"
    ])

    r = requests.get(video_info_url, headers=headers)

    return r.json()



def get_video_url(metadata, resolution):

    for element in metadata['data']['videosBySlugs']['elements']:
        if element.get('entityType') != "VIDEO":
            continue
        streams = element['presentationDerived']['videoPlay']['videoPlayMetadata']['progressiveStreams']

        # Determine resolution closest to preference
        best_res = [{'height': 0}, 999999]
        for stream in streams:
            diff = abs(resolution - stream['height'])
            if diff < best_res[1]:
                best_res = [stream, diff]
                if diff == 0:
                    break

        return best_res[0]['streamingLocations'][0]['url']


def download(u, p):
	r = requests.get(u, stream=True, headers=h)
	with open(p,'wb') as o:
		o.write(r.content)

r = s.get(u, headers=h_guest, allow_redirects=False)
soup = BeautifulSoup(html.unescape(r.text), 'html.parser')

course = []
for section in soup.select('.toc-section'):
	
	name = section.select_one('button').get_text(strip=True)
	obj = {'section': name, 'items': [], 'links':[] }
	print(name)
	for li in section.select('.toc-item'):
		
		for x in li.select('.table-of-contents__item-title'):
			obj['items'].append(x.get_text(strip=True).title())

		for a in li.find_all('a', href=True):
			obj['links'].append(a['href'].split("?")[0])
	
	course.append(obj)


if not os.path.exists(f'{base_path}/{ctitle}/video'):
    os.makedirs(f'{base_path}/{ctitle}/video')

headers = {
    'X-RestLi-Protocol-Version': '2.0.0',
    'Csrf-Token': jsession,
    'Cookie': f'JSESSIONID={jsession}; li_at="{li_at}"'
}
for sn, section in enumerate(course):
    print(section['section'])
    name = f'{sn+1:02d} + ' + re.sub(r"^\d.\s*", "", section['section'].strip())

    section_path = f'{base_path}/{ctitle}/video/{clean_dir(name).replace("-", " ").replace("+", "-").title()}'
    if not os.path.exists(section_path):
        os.mkdir(section_path)

    for n, item in enumerate(section['items'], 0):

        video_slug = section['links'][n].split("/")[-1]

        vname = f'{sn+1:02d}.{n+1:02d} - {video_slug.replace("-", " ").title()}.mp4'
        vpath = f'{section_path}/{vname}'

        print("Downloading:", vname)
        if os.path.exists(vpath) and skip:
            print("Video already exists, skipping...")
            continue

        metadata = get_video_metadata(slug, video_slug, headers)
        vurl = get_video_url(metadata, int(res))
        if vurl:
            download(vurl, vpath)
