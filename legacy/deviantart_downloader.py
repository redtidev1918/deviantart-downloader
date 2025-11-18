import html
import json
import os.path
import sys
from time import sleep
from typing import Dict, Optional

import requests
import requests.adapters
from requests.exceptions import ChunkedEncodingError, ConnectionError, ProxyError, SSLError

if len(sys.argv) <= 1 or sys.argv[1] in ['-h', 'help']:
    print('''
╔══════════════════════════════════════════════════════════════════════╗
║             DEVIANTART DOWNLOADER - HELP & USAGE GUIDE               ║
╚══════════════════════════════════════════════════════════════════════╝

ACTION TYPES:
  gallery <PROFILE_NAME>              [OPTIONS]  - Download all arts from profile
  gallery <PROFILE_NAME> <GALLERY_ID> [OPTIONS]  - Download specific gallery
  search  <PROFILE_NAME> <QUERY>      [OPTIONS]  - Search within a profile
  search  all            <QUERY>      [OPTIONS]  - Global search on DeviantArt
  fav     <PROFILE_NAME> <FOLDER_ID>  [OPTIONS]  - Download favourite folder

OPTIONS:
  --ask=<0|1>         Ask before each download (default: 1)
  --cookies=<PATH>    Path to cookies file (default: ./cookies.txt)
  --debug=<0|1>       Debug mode (default: 0)
  --delay=<DECIMAL>   Delay between downloads in seconds (default: 1)
  --dest=<PATH>       Destination folder for downloads
  --limit=<1..60>     Lazy loading limit (default: 24)
  --offset=<INT>      Beginning offset (default: 0)
  --proxy=<URL>       Proxy server (e.g. http://127.0.0.1:8580)
  --quality=<o|f|p>   Quality: o=original, f=full, p=preview (default: o)
  --replace=<0|1>     Replace existing files (default: 1)
  --separate=<0|1>    Separate folders per profile (default: 1 for gallery)

INTERACTIVE ANSWERS:
  q, quit              Quit the application
  s, skip              Skip current batch of items
  a, all               Download all remaining items
  y, yes               Download current item
  p, pre, preview      Download in preview quality
  f, ful, full         Download in full-view quality
  o, org, original     Download in original quality
  <Enter/other>        Skip current item

LOGIN & AUTHENTICATION:
  ✓ The script now has IMPROVED LOGIN support!
  ✓ Automatically validates your cookies
  ✓ Interactive guide to help you get cookies
  ✓ Better error messages when login is required
  
  To use login features:
  1. Create a file named "cookies.txt" in this folder
  2. Add your DeviantArt cookies (the script will guide you)
  3. Run the script - it will validate your login automatically
  
  Login is REQUIRED for:
  • Downloading original quality images (--quality=o)
  • Accessing private/exclusive content
  • Viewing mature content (if age-restricted)

EXAMPLES:
  python deviantart_downloader.py gallery username
  python deviantart_downloader.py gallery username --quality=f --ask=0
  python deviantart_downloader.py search username "landscape" --limit=50
  python deviantart_downloader.py fav username 123456 --dest=./favorites

NOTE: If you see censored mature content, you've been logged out!
''')
    quit()

OPT_ASK = '--ask'
OPT_COOKIES = '--cookies'
OPT_DEBUG = '--debug'
OPT_DELAY = '--delay'
OPT_DEST = '--dest'
OPT_LIMIT = '--limit'
OPT_OFFSET = '--offset'
OPT_PROXY = '--proxy'
OPT_QUALITY = '--quality'
OPT_REPLACE = '--replace'
OPT_SEPARATE = '--separate'

ANS_QUIT = 'q', 'Q', 'quit'
ANS_SKIP = 's', 'S', 'skip'
ANS_ALL = 'a', 'A', 'all'
ANS_YES = 'y', 'Y', 'yes'
ANS_PRE = 'p', 'P', 'pre', 'preview'
ANS_FUL = 'f', 'F', 'ful', 'full'
ANS_ORG = 'o', 'O', 'org', 'original'

# parse arguments
lazy = '&offset=<OFFSET>&limit=<LIMIT>'
pattern, username, kvOptions, da_browse_api = '', sys.argv[2].lower(), list(), False
if sys.argv[1] == 'gallery':
    pattern = ('https://www.deviantart.com/_puppy/dashared/gallection/contents?username=' +
               username + '&type=gallery' + lazy + '&csrf_token=<CSRF>')
    if len(sys.argv) <= 3 or '=' in sys.argv[3]:
        pattern += '&all_folder=true'
        kvOptions = sys.argv[3:]
    else:
        pattern += '&folderid=' + sys.argv[3]  # is 46658611 always for FEATURED?
        kvOptions = sys.argv[4:]
elif sys.argv[1] == 'search':
    if len(sys.argv) <= 3:
        print('Missing arguments!')
        quit()
    if username != 'all':
        pattern = ('https://www.deviantart.com/_puppy/dashared/gallection/search?username=' +
                   username + '&type=gallery&order=most-recent&q=' + sys.argv[3] + '&init=true' + lazy +
                   '&csrf_token=<CSRF>')
    else:
        pattern = ('https://www.deviantart.com/_puppy/da-browse/api/networkbar/search/deviations?q=' +
                   sys.argv[3] + '&cursor=<CURSOR>' + '&csrf_token=<CSRF>')
        da_browse_api = True
    kvOptions = sys.argv[4:]
elif sys.argv[1] == 'fav':
    if len(sys.argv) <= 3:
        print('Missing arguments!')
        quit()
    pattern = ('https://www.deviantart.com/_puppy/dashared/gallection/contents' +
               '?username=' + username + '&type=collection' + lazy + '&folderid=' + sys.argv[3] +
               '&csrf_token=<CSRF>')
    kvOptions = sys.argv[4:]
else:
    print('Unknown command', sys.argv[1])
    quit()

# parse the options
opt = {
    OPT_ASK: '1',
    OPT_COOKIES: None,
    OPT_DEBUG: '0',
    OPT_DELAY: '1',
    OPT_DEST: None,
    OPT_LIMIT: '24',
    OPT_OFFSET: '0',
    OPT_PROXY: '',
    OPT_QUALITY: 'o',
    OPT_REPLACE: '1',
    OPT_SEPARATE: '1' if sys.argv[1] == 'gallery' else '0',
}
for kv in kvOptions:
    s = kv.split('=')
    opt[s[0]] = s[1]


def load_cookies() -> str:
    """ Load optional cookies from a file. """
    path = opt[OPT_COOKIES]
    if path is None:
        path = 'cookies.txt'
    if os.path.isfile(path):
        with open(path, 'r') as f:
            cookies = f.read().strip()
        if cookies:
            print(f'✓ Loaded cookies from: {path}')
            return cookies
        else:
            print(f'WARNING: Cookie file is empty: {path}')
            return ''
    print(f'INFO: No cookie file found at {path} (optional for public content)')
    return ''


def validate_cookies(cookies: str) -> bool:
    """ Validate if cookies contain authentication tokens. """
    if not cookies:
        return False
    # Check for common DeviantArt auth cookies
    auth_indicators = ['auth=', 'auth_secure=', 'userinfo=']
    return any(indicator in cookies for indicator in auth_indicators)


def show_login_guide():
    """ Display interactive guide for obtaining cookies. """
    print('''
╔══════════════════════════════════════════════════════════════════════╗
║                    HOW TO GET DEVIANTART COOKIES                     ║
╚══════════════════════════════════════════════════════════════════════╝

1. Open DeviantArt in your browser and LOGIN to your account
   → https://www.deviantart.com

2. Open Browser Developer Tools:
   • Chrome/Edge: Press F12 or Ctrl+Shift+I (Cmd+Option+I on Mac)
   • Firefox: Press F12 or Ctrl+Shift+I (Cmd+Option+I on Mac)

3. Go to "Application" tab (Chrome) or "Storage" tab (Firefox)

4. In the left sidebar, expand "Cookies" and click on:
   → https://www.deviantart.com

5. Copy ALL cookie values in this format:
   cookie1=value1; cookie2=value2; cookie3=value3

   Important cookies to include:
   • auth
   • auth_secure
   • userinfo

6. Paste the copied cookies into a file named "cookies.txt"
   in the same folder as this script

Alternatively, you can use browser extensions like:
• "EditThisCookie" (Chrome)
• "Cookie-Editor" (Firefox/Chrome)

''')


def check_login_status() -> bool:
    """ Check if user is logged in by verifying CSRF token retrieval. """
    try:
        test_page = requests.get('https://www.deviantart.com', headers=headers, proxies=proxies, timeout=10)
        # If we can find user-specific content, we're logged in
        if 'window.__CSRF_TOKEN__' in test_page.text:
            if 'data-userid' in test_page.text or '"isLoggedIn":true' in test_page.text:
                print('✓ Successfully logged in!')
                return True
            else:
                print('! Not logged in (public access only)')
                return False
    except Exception as e:
        print(f'! Could not verify login status: {e}')
        return False


# HTTP headers and proxies
cookies_str = load_cookies()
headers: dict[str, str] = {
    "accept": "application/json, text/plain, */*",
    "cookie": cookies_str
}
proxies = {'https': opt[OPT_PROXY]}

# Validate cookies if provided
if cookies_str:
    if validate_cookies(cookies_str):
        print('✓ Cookies appear valid (contains auth tokens)')
    else:
        print('⚠ Warning: Cookies may be invalid or incomplete')
        answer = input('Do you want to see the cookie setup guide? (y/n): ').lower()
        if answer in ['y', 'yes']:
            show_login_guide()
else:
    print('! Running without cookies - only public content accessible')
    if opt[OPT_QUALITY] == 'o':
        print('\n⚠ WARNING: Original quality downloads require login!')
        answer = input('Show login guide? (y/n): ').lower()
        if answer in ['y', 'yes']:
            show_login_guide()
            input('\nPress Enter after setting up cookies, or Ctrl+C to exit...')
            # Reload cookies
            cookies_str = load_cookies()
            headers["cookie"] = cookies_str

# settings and constants
requests.adapters.DEFAULT_RETRIES = 6
delay_before_retry: int = 3
download_link_starter: str = 'https://www.deviantart.com/download/'
default_downloads_folder: str = 'Downloads'
find = lambda my_list, b: [x for x in my_list if b(x)][0]

# miscellaneous
html_text: Optional[str] = None

# get CSRF token and if necessary the userId
page: Optional[str] = None
retry_count = 0
max_retries = 3
while page is None:
    try:
        page = requests.get('https://www.deviantart.com/' + username, headers=headers, proxies=proxies).text
    except (ConnectionError, ProxyError, SSLError) as e:
        retry_count += 1
        if retry_count >= max_retries:
            print(f'\n✗ Failed to connect after {max_retries} attempts')
            print('Please check your internet connection or proxy settings')
            quit()
        print(f'Retrying for CSRF... ({retry_count}/{max_retries})', '(' + str(type(e).__name__) + ')')
        sleep(delay_before_retry)

# Check if user exists
if '404' in page or 'Page Not Found' in page:
    print(f'\n✗ User "{username}" not found!')
    print('Please check the username and try again.')
    quit()

page = page[page.index('window.__BASEURL__'):]
page = page[0:page.index('</script>')]
befCsrf, aftCsrf = 'window.__CSRF_TOKEN__ = \'', '\';'
if befCsrf not in page:
    print('\n✗ Couldn\'t find the crucial CSRF token!')
    print('The page structure may have changed. Please report this issue.')
    quit()
csrf = page[page.index(befCsrf) + len(befCsrf):]
csrf = csrf[0:csrf.index(aftCsrf)]
print(f'✓ CSRF token acquired')
pattern = pattern.replace('<CSRF>', csrf)

# Check login status
if cookies_str:
    check_login_status()

del page, befCsrf, aftCsrf


# noinspection PyShadowingNames
def fetch(url: str, offset: int, next_cursor: str = ''):
    """ `offset` is for the Shared API and `next_cursor` for the DA-Browse API. """

    # fetch a list from the DeviantArt API
    api_res = None
    while api_res is None:
        try:
            api_res = requests.get(
                url.replace('<OFFSET>', str(offset)).replace('<CURSOR>', next_cursor),
                headers=headers, proxies=proxies).text
        except (ConnectionError, ProxyError, SSLError):
            print('Retrying for API...')
            sleep(delay_before_retry)

    # parse the list
    data: Dict = json.loads(api_res)
    del api_res
    if 'errorCode' in data:
        print(url.replace('<OFFSET>', str(offset)).replace('<CURSOR>', next_cursor))
        print(json.dumps(data))
        return
    if 'results' not in data and 'deviations' not in data:
        print('NOTHING FOUND!')
        print(json.dumps(data))
        return
    arr = data['results'] if 'results' in data else data['deviations']
    print('Fetched ' + str(len(arr)) + ' items.')

    # BEGIN LOOPING
    skip_yes = False
    iArt = offset - 1
    for art in arr:
        iArt += 1
        deviation = art if 'deviation' not in art else art['deviation']
        if opt[OPT_DEBUG] == '1':
            print(json.dumps(deviation))
        if deviation['type'] in ['literature']:
            print('[' + str(iArt) + ']: Skipped an item because it\'s not downloadable.')
            continue

        # specify the branch directory
        if opt[OPT_DEST] is not None:
            if opt[OPT_SEPARATE] == '1':
                branch = os.path.join(opt[OPT_DEST], deviation['author']['username'])
            else:
                branch = opt[OPT_DEST]
        else:
            if opt[OPT_SEPARATE] == '1':
                branch = deviation['author']['username']
            else:
                branch = default_downloads_folder
        if not os.path.isdir(branch):
            os.mkdir(branch)

        # prepare a destination for the output file to be saved
        media: Dict = deviation['media']
        file_type = media['baseUri'].split('.')
        file_type = '.' + file_type[len(file_type) - 1]
        file_path = os.path.join(branch, media['prettyName'] + file_type)
        already_exists = os.path.isfile(file_path)
        if already_exists and opt[OPT_REPLACE] == '0':  # and opt[OPT_QUALITY] != 'o'
            print('[' + str(iArt) + ']: SKIPPED', media['prettyName'])
            continue

        # ask the user if necessary
        quality = opt[OPT_QUALITY]
        if opt[OPT_ASK] == '1' and not skip_yes:
            title_suffix = ''
            if deviation['isMature']:
                title_suffix += ' -- !MATURE CONTENT!'
            if already_exists:
                title_suffix += ' -- !ALREADY DOWNLOADED!'
            ans = input('[' + str(iArt) + ']: ' +
                        deviation['title'] + title_suffix + '\n' + deviation['url'] + '\n')

            if ans in ANS_QUIT:
                quit()
            elif ans in ANS_SKIP:
                break
            elif ans in ANS_ALL:
                skip_yes = True
            elif ans in ANS_YES:
                pass
            elif ans in ANS_PRE:
                quality = 'p'
            elif ans in ANS_FUL:
                quality = 'f'
            elif ans in ANS_ORG:
                quality = 'o'
            else:
                continue

        # prepare to download an original view if desired
        if quality == 'o' and deviation['isDownloadable']:
            find_download_button(deviation)
            global html_text
            login_attempts = 0
            while download_link_starter not in html_text:
                if login_attempts == 0:
                    print('\n' + '='*70)
                    print('⚠  LOGIN REQUIRED TO DOWNLOAD ORIGINAL QUALITY')
                    print('='*70)
                    show_login_guide()
                    print('='*70)
                login_attempts += 1
                cmd = input('\nAfter updating cookies.txt, press ENTER to retry (or "q" to quit): ')
                if cmd in ANS_QUIT:
                    quit()
                new_cookies = load_cookies()
                if not new_cookies:
                    print('✗ Still no cookies found!')
                    continue
                headers['cookie'] = new_cookies
                if validate_cookies(new_cookies):
                    print('✓ New cookies loaded, retrying download...')
                else:
                    print('⚠ Warning: Cookies may be invalid')
                find_download_button(deviation)
            download = html.unescape(
                download_link_starter + html_text.split(download_link_starter)[1].split('\"')[0])
            file_type = download.split('?')[0].split('.')
            file_type = '.' + file_type[len(file_type) - 1]
            file_path = os.path.join(branch, media['prettyName'] + file_type)
            if os.path.isfile(file_path) and opt[OPT_REPLACE] == '0':
                print('SKIPPED', media['prettyName'])
                continue

        # prepare to download a full view if desired
        elif quality == 'f' or (quality == 'o' and not deviation['isDownloadable']):
            full_view = find(media['types'], lambda x: x['t'] == 'fullview')
            if 'c' in full_view:
                download = media['baseUri'] + full_view['c'].replace('<prettyName>', media['prettyName'])
                if 'token' in media: download += '?token=' + media['token'][0]
            # if 'c' is already in 'fullview' and you acquire the raw 'baseUri', it'll give you 403 error!
            else:
                download = media['baseUri']
                if 'token' in media: download += '?token=' + media['token'][0]

        # prepare to download a preview if desired
        else:
            # all the other sources are just thumbnails, avoid them all.
            # mostly 'social_preview' and 'preview' are equal; but sometimes social preview
            # refers to https://st.deviantart.net/misc/noentrythumb-200.png with 200x200 dimensions.
            pre_view = find(media['types'], lambda x: x['t'] == 'preview')
            if 'c' in pre_view:
                src = pre_view['c']
            else:
                print('COULD NOT FIND A PROPER URL FOR', deviation['url'])
                continue
            download = media['baseUri'] + src.replace('<prettyName>', media['prettyName'])
            if 'token' in media: download += '?token=' + media['token'][0]

        # download the desired file
        binary = None
        while binary is None:
            try:
                binary = requests.get(
                    download, headers=headers, proxies=proxies, allow_redirects=True, timeout=180).content
            except (ConnectionError, ProxyError, SSLError, ChunkedEncodingError):
                print('Retrying for the image binary...')
                sleep(delay_before_retry)
        wrote = False
        while not wrote:
            try:
                open(file_path, 'wb').write(binary)
                wrote = True
            except OSError:
                input("Please close the existing file and then hit Enter...")
        del binary, wrote
        print('[' + str(iArt) + ']: Downloaded', media['prettyName'] + file_type)
        if opt[OPT_ASK] == '0' and not skip_yes:
            sleep(float(opt[OPT_DELAY]))
    # ENF OF LOOPING

    if data['hasMore']:
        fetch(url, data['nextOffset'] if not da_browse_api else iArt,
              data['nextCursor'] if 'nextCursor' in data else '')
    else:
        print('END OF LIST.')


def find_download_button(deviation: Dict):
    """ Find the download button inside an HTML file of DeviantArt. """
    global html_text
    got_it = False
    while not got_it:
        try:
            html_text = requests.get(deviation['url'], headers=headers, proxies=proxies).text
            got_it = True
        except (ConnectionError, ProxyError, SSLError):
            print('Retrying for the download button...')
            sleep(delay_before_retry)


fetch(pattern.replace('<LIMIT>', opt[OPT_LIMIT]), int(opt[OPT_OFFSET]))
