
from datetime import datetime
from selenium import webdriver
from haversine import haversine
from folium.features import DivIcon
from email.mime.text import MIMEText
import requests
import json
import time
import googlemaps
import folium
import polyline
import os
import boto3
import smtplib
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from PIL import Image as pil#이미지 처리 pip install pillow
from selenium.webdriver import ActionChains#스크롤처리
import telegram
from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters

#텔레그램 공고요청
token = '텔레그램 키'
bot = telegram.Bot(token=token)
updates = bot.getUpdates()
# for u in updates:
#     print(u.message.chat.id)
   
# for u in updates:
#         chat = u.message.text
#         id = u.message.chat.id
#         print(u.message.text)

# Saramin API
key = "사람인키" # 엑세스 키값
loc_cd = "101000" # 지역코드 -> 서울 전체
loc_mcd = "102180" # 지역코드 -> 성남시
# published = str(year) + "-" + str(month) + "-" + str(day) # 등록일 yyyy-mm-dd
# published = "2021-09-07"
# keyword = ['python', 'sql', 'data engineer']
# print(published)

# Google Maps
gmaps_key = "구글맵키"
gmaps = googlemaps.Client(key=gmaps_key)
home = '성남 송현초등학교'

#Chrome Driver Options
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument("disable-gpu")


#사람인 api
def Saramin(keyword, count):
    # 10 110
    print('사람인 검색 단어-->',keyword, count)
    URL = "https://oapi.saramin.co.kr/job-search?access-key=%s&keywords=%s&loc_cd=%s&loc_mcd=%s&count=110&fields=count" % (key,keyword,loc_cd, loc_mcd)
    print(URL)
    # API를 통해 Json 형태로 데이터 추출
    response = requests.get(URL)
    data = response.json()
#     print("사람인응답=>",data)
    # 데이터 전처리
    new_data = []
    for i in range(len(data['jobs']['job'])):
        if data['jobs']['job'][i]['position']['experience-level']['code'] != 2: # 신입(0), 경력무관(1), 경력(2)
            new_data.append(data['jobs']['job'][i])

    # 원하는 요소 추출
    company = [] # 회사명
    title = [] # 공고명
    location = [] # 회사 위치
    expiration_date = [] # 공고 마감일
    com_url = [] # 공고 URL
    apply_cnt = [] # 현재 지원자수
    for i in range(len(new_data)):
        com_url.append(new_data[i]['url'])
        company.append(new_data[i]["company"]["detail"]["name"].replace("(주)", ""))
        title.append(new_data[i]["position"]["title"])
        loc = new_data[i]["position"]["location"]["name"].split(" &gt; ")
        loc_res = (loc[0] + " " + loc[1])
        location.append(loc_res)
        dt_FromTs = new_data[i]['expiration-timestamp']
        expiration_date.append(str(datetime.fromtimestamp(int(dt_FromTs))))
        apply_cnt.append(new_data[i]['apply-cnt'])
#     print("=>",len(company))
    # 2차원 리스트로 변환
    com_list = []
    for i in range(len(company)):
        com_list.insert(i, [company[i], title[i], location[i], expiration_date[i], com_url[i], apply_cnt[i]])
    return com_list


# bot.sendMessage(chat_id=id, text={len(company)}+"개의 공고를 찾았습니다. 잠시 후 보내드리겠습니다.")
# webdriver 접속
def jobplanet(company,a, index):
    print('job')
    driver = webdriver.Chrome('chromedriver')
    # driver = webdriver.Chrome('chromedriver', chrome_options=options) # headless 적용
    driver.get("https://www.jobplanet.co.kr/")
    driver.maximize_window()
    driver.implicitly_wait(5)

    # 로그인 버튼 클릭
    login_link = driver.find_element_by_css_selector('a.btn_txt.login')
    login_link.click()
    driver.implicitly_wait(5)

    # 페이스북으로 로그인
    fb_link = driver.find_element_by_css_selector('#signInSignInCon > div.signInsignIn_wrap > div > section.section_facebook > a')
    fb_link.click()
    driver.implicitly_wait(5)

    # id 입력
    username_input = driver.find_element_by_css_selector('#email')
    username_input.send_keys("잡플래닛ID")

    # password 입력
    password_input = driver.find_element_by_css_selector('#pass')
    password_input.send_keys("잡플래닛PW") 
    driver.find_element_by_css_selector('#loginbutton').click()
    driver.implicitly_wait(5)

    # 권한 확인 인터페이스 신규 생성으로 인한 코드 추가 20201119
    # driver.find_element_by_tag_name('body').send_keys(Keys.ESCAPE)
    # driver.implicitly_wait(5)
    # auth_bttn = driver.find_element_by_css_selector('#platformDialogForm > div._5lnf.uiOverlayFooter._5a8u > table > tbody > tr > td._51m-.prs.uiOverlayFooterMessage > table > tbody > tr > td._51m-.uiOverlayFooterButtons._51mw > button._42ft._4jy0.layerConfirm._51_n.autofocus._4jy5._4jy1.selected._51sy')
    # auth_bttn.click()

    # 회사명 검색
#     for i in range(len(a)):
    driver.get("https://www.jobplanet.co.kr/")
    driver.implicitly_wait(5)
    driver.get("https://www.jobplanet.co.kr/companies/cover")
    driver.implicitly_wait(5)
    search_com = driver.find_element_by_css_selector('#search_bar_search_query')
    search_com.send_keys(a)
    # driver.find_element_by_css_selector('#search_form > div > div > button').click()
    driver.find_element_by_css_selector('#search_form > div > button').click()
    driver.implicitly_wait(5)
#     print(a)

    # 예외 처리
    try:
        driver.find_element_by_css_selector('#mainContents > div:nth-child(1) > div > div.result_company_card > div.is_company_card > div > a').click()
        driver.implicitly_wait(5)

        # 점수
        # score = driver.find_element_by_css_selector('body > div.body_wrap > div.cmp_hd > div.new_top_bnr > div > div.top_bnr_wrap > div > div > div.company_info_sec > div.company_info_box > div.about_company > div.grade.jply_ico_star > span').text
        score = driver.find_element_by_css_selector('body > div.body_wrap > div.cmp_hd > div.new_top_bnr > div > div.top_bnr_wrap > div > div > div.company_info_sec > div.company_info_box > div.about_company > div.score_area.type_total_year > div > span').text
        # 현재 페이지의 후기
        dg = driver.page_source # 현재 페이지
        soup = BeautifulSoup(dg, 'html.parser')
        comment_raw = soup.find_all("h2", {"class" : "us_label"})
        comments = [comment.text for comment in comment_raw]
        for j in range(len(comments)):
            comments[j] = comments[j].replace("\nBEST\n      \"", "")
            comments[j] = comments[j].replace("\n", " ")
            comments[j] = comments[j].replace("\"     ", "")

        company[index].append(score)
        if len(comments) != 0:
            company[index].append(comments)
        else:
            company[index].append([])

    except: # 회사가 존재하지 않을경우
        company[index].append('없음') # 평점 0 
        company[index].append([])
        # company[i].append(["없음"]) # 후기 빈 리스트로 추가
    driver.quit()
# mail에 첨부할 텍스트 전처리
def extract_mail(company):
    list_num = ['①', '②', '③', '④', '⑤']
    mail_text = []
    print('mail_text->',company)
#     for i in range(len(company)):
    mail_text.append('회    사 : {com}'.format(com = company[0]))
    mail_text.append('공 고 명 : {com}'.format(com = company[1]))
    mail_text.append('위    치 : {com}'.format(com = company[2]))
    mail_text.append('지 원 자 : {com}명'.format(com = company[5]))
    mail_text.append('마 감 일 : {com}'.format(com = company[3]))
    mail_text.append('평    점 : {com}'.format(com = company[6]))
    mail_text.append('공    고 : {com}'.format(com = company[4]))

    if len(company[7]) == 0:
        mail_text.append('후    기 : {com}'.format(com = "없음"))
    else:
        mail_text.append('후    기 :')
        for j in range(len(company[7])):
            mail_text.append('{num} {com}'.format(num = list_num[j], com = company[7][j]))
    mail_text.append(' ')

    mail_text = "\n".join(mail_text) + "\n"
    return mail_text

# 입력한 위치의 위도, 경도를 출력
def val_lat_lng(loc):
    user_info = gmaps.geocode(loc, language = 'ko')
    user_geo = user_info[0].get('geometry')
    user_lat = user_geo['location']['lat'] # 위도
    user_lng = user_geo['location']['lng'] # 경도
    loc_val = [user_lat, user_lng]
    return loc_val

#구글맵
def loc_map(com):
    loc_com = val_lat_lng(com) # 회사 위도 & 경도
    loc_home = val_lat_lng(home) # 집 위도 & 경도
    loc_center = [round((loc_com[0] + loc_home[0])/2, 7), round((loc_com[1] + loc_home[1])/2, 7)]
    
    # 길찾기
    print(home,com)
    directions_result = gmaps.directions(home, com, mode = "transit") # departure_time = datetime.now()
    
    # 집과 회사의 거리차에 따른 zoom
    hc_distance = round(haversine(loc_home, loc_com), 2)
    if hc_distance < 6:
        zoom_start = 14
    elif hc_distance >= 6 and hc_distance < 12:
        zoom_start = 13
    elif hc_distance >= 12 and hc_distance < 24:
        zoom_start = 12
    elif hc_distance >= 24 and hc_distance < 48:
        zoom_start = 11
    else:
        zoom_start = 10
        #print(hc_distance, zoom_start)

    g_map = folium.Map(location = loc_center, zoom_start = zoom_start)
    duration = directions_result[0]['legs'][0]['duration']['text'].replace(" hours", "시간").replace(" hour", "시간").replace(" mins", "분") # 소요 시간
    distance = directions_result[0]['legs'][0]['distance']['text'].replace(" km", "km") # 거리

    # Polyline Decode
    for i in range(len(directions_result[0]['legs'][0]['steps'])):
        a = directions_result[0]['legs'][0]['steps'][i]
        b = polyline.decode(a['polyline']['points'])
        # c = (a['start_location']['lat'], a['end_location']['lng'])
        # folium.Marker(c).add_to(g_map)
        folium.PolyLine(b, color="red", weight=8, opacity=1).add_to(g_map)

    folium.Marker(
        location = (directions_result[0]['legs'][0]['start_location']['lat'], directions_result[0]['legs'][0]['start_location']['lng']),
        popup = 'Home',
        icon = folium.Icon(color='blue',icon='star')    
    ).add_to(g_map)

    folium.Marker(
        location = (directions_result[0]['legs'][0]['end_location']['lat'], directions_result[0]['legs'][0]['end_location']['lng']),
        tooltip = 'company',
        popup = '''
            Company
            Duration : %s
            Distance : %s
        ''' % (directions_result[0]['legs'][0]['duration']['text'], directions_result[0]['legs'][0]['distance']['text']),
        icon = folium.Icon(color='blue',icon='star')
    ).add_to(g_map)

    html = '''
    <div style="font-size: 24pt">Distance : {a}</div>
    <div style="font-size: 24pt">Duration : {b}</div>
    '''.format(a=distance, b = duration)

    folium.Marker(
        location = loc_center,
        icon = DivIcon(
            icon_size=(600,36),
            icon_anchor=(0,0),
            html = html,
        )
    ).add_to(g_map)
    
    return g_map

# 지도 html을 png 파일로 생성
def make_png(g_map, company_name):
    delay = 5
    fn = 'map.html'
    tmpurl='file://{path}/{mapfile}'.format(path=os.getcwd(),mapfile=fn)
    g_map.save(fn)
    browser = webdriver.Chrome('chromedriver', chrome_options=options) # headless 적용
    browser.get(tmpurl)
    #Give the map tiles some time to load
    time.sleep(delay)
    browser.save_screenshot('{day}_{com}.png'.format(day = "map", com = company_name)) # 2020-01-01_회사명.png
    browser.quit()
    
#CreditJob 메서드
def Kredit_Job(a):
    #webdriver 접속
    print(a)
    driver = webdriver.Chrome('chromedriver')
#     driver = webdriver.Chrome(chromedriver,options=options) # headless 적용
    driver.get("https://kreditjob.com/")
#     driver.maximize_window()
    driver.set_window_size(1920, 1080)
    driver.implicitly_wait(5)
    
    #회사명 검색 
    for i in range(len(a)):
        driver.get("https://kreditjob.com/")
        driver.implicitly_wait(5)
        search=driver.find_element_by_css_selector('div.body-container>div.home-wrapper>div.col-xs-12>div.home-search-box-container>div.search-box-wrapper>div.search-box-query-box>div.react-autosuggest__container>input.search-query')
        search.send_keys( a[i].replace("(주)",""))
        driver.find_element_by_css_selector('div.body-container>div.home-wrapper>div.col-xs-12>div.home-search-box-container>div.search-box-wrapper>div.search-box-query-box>div.react-autosuggest__container>input.search-query').send_keys(Keys.ENTER)        
        tmp_cname=driver.find_element_by_css_selector('div.body-container>div.company-container>div.company-wrapper>div.company-contents>section.company-label-container>div.label-container>div.info-box>div.company-label>span.company-name')      
        try:
            #스크롤할 부분 찾기
            print(1)
            some_tag = driver.find_element_by_css_selector('div.body-container>div.company-container>div.company-wrapper>div.company-contents>section.company-salary-container>div>p.wikiInfo')
            driver.implicitly_wait(5)
            
            #스크롤 내리기 
            print(2)
            action = ActionChains(driver)
            action.move_to_element(some_tag).perform()
            driver.implicitly_wait(5)
            
            #편집할 이미지 
            print(3)
            driver.save_screenshot('salary'+str(i)+'.png')
            print(a[i]+'캡쳐완료')
            
            #이미지 전체크기 확인
            pil_im=pil.open('salary'+str(i)+'.png')
            
            #원하는 이미지영역 크기 확인 
            element = driver.find_element_by_css_selector('div.body-container>div.company-container>div.company-wrapper>div.company-contents>section.company-salary-container>div')
            location=element.location
            size=element.size
            print(location,size)
            
            #이미지 영역 계산
            left = location['x']
            top = location ['y']
            right = left+size['width']
            bottom = top+size['height']
            area = (left, 217, right, bottom)
            
            #이미지 잘라내기
            pil_im = pil_im.crop(area)
            print(a[i]+'잘라내기 완료')
            pil_im.save(a[i]+'.png')
            
        except:
             print(a[i]+'이미지 처리 실패')
                                         
    return a[i]+'.png';


#텔레그램 챗봇
bot = telegram.Bot(token)

 
# updater
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher
updater.start_polling()

company = ''
word = ''
count = ''

# 사용자가 보낸 메세지를 읽어들이고, 답장을 보내줍니다.
# 아래 함수만 입맛에 맞게 수정해주면 됩니다. 다른 것은 건들 필요없어요.
def handler(update, context):
        print(update.message.chat.id)
        print(update.message.text)
        global word
        global count #요청받을 공고 개수
        id = update.message.chat.id
        user_text = update.message.text # 사용자가 보낸 메세지를 user_text 변수에 저장합니다.
        if user_text == "공고": # 사용자가 보낸 메세지가 "안녕"이면?
            bot.send_message(chat_id=id, text="받으실 공고개수를 선택해주세요. 10개미만 ")
            user_text =''
        if len(user_text) == 1:
            count = user_text
            bot.send_message(chat_id=id, text="검색내용을 입력해주세요. 2자 이상 \n ex)자바, 백엔드")
            user_text ='' 
        if len(user_text)>1:      #사람인 데이터 호출   # Job Planet에 사용할 회사명 리스트
            word = user_text
            company = Saramin(word, count) # 회사명, 공고명, 지역명, 마감일, URL
            com_count = len(company)
            bot.send_message(chat_id=id, text=str(com_count)+"개 공고를 찾았습니다. 크롤링 중입니다. 좀 기다려주세요ㅠㅜ..순차적으로 발송됩니다.")
            print(len(company))
#             print(company)
            a = []
            for i in range(int(count)):
                a.append(company[i][0])
                print('a->',a)
                jobplanet(company,company[i][0], i)
#                 print('company->', company[i])
                data = extract_mail(company[i])
                image = Kredit_Job(a)
                photo_list = []
                photo_list.append(telegram.InputMediaPhoto(open("./"+image, "rb")))
                try:
                    g_map = loc_map('엔키아')
                    make_png(g_map, '엔키아')
#                     to_s3(i, com) # URL
                    print("map 성공")
                    photo_list.append(telegram.InputMediaPhoto(open("./"+"map_"+"엔키아.png", "rb")))
                except:
#                     company[i].append("없음")
                    print("map 실패")
                bot.send_message(chat_id=id, text=data)
                bot.sendMediaGroup(chat_id=id, media=photo_list)
#             jobplanet(company,a)
            
            print("====")
#             print(len(data))
#             bot.send_message(chat_id=id,text=data) # 답장 보내기
        if user_text !='':
            keyword = user_text
            user_text ='' 
            bot.sendMessage(chat_id=id, text="'공고' 라고 입력하시면 정보를 받으실 수 있습니다.")
        elif user_text == "뭐해": # 사용자가 보낸 메세지가 "뭐해"면?
            bot.send_message(chat_id=id, text="그냥 있어") # 답장 보내기

echo_handler = MessageHandler(Filters.text, handler)
dispatcher.add_handler(echo_handler)

