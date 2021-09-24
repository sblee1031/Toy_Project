
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

import telegram
from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters

#텔레그램 공고요청
token = '텔레그램API'
bot = telegram.Bot(token=token)
updates = bot.getUpdates()
for u in updates:
    print(u.message.chat.id)
   
# for u in updates:
#         chat = u.message.text
#         id = u.message.chat.id
#         print(u.message.text)

# Saramin API
key = "사람인키" # 엑세스 키값
loc_cd = "101000+102180" # 지역코드 -> 서울 전체 + 분당
# published = str(year) + "-" + str(month) + "-" + str(day) # 등록일 yyyy-mm-dd
published = "2021-09-07"
# keyword = ['python', 'sql', 'data engineer']
# print(published)

#사람인 api
def Saramin(keyword, count):
    # 10 110
    print('사람인 검색 단어-->',keyword, count)
    URL = "https://oapi.saramin.co.kr/job-search?access-key=%s&keywords=%s&loc_cd=%s&loc_mcd=%s&count=110&fields=count" % (key,keyword,loc_cd, loc_mcd)
    print(URL)
    # API를 통해 Json 형태로 데이터 추출
    response = requests.get(URL)
    data = response.json()
    print("사람인응답=>",data)
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
    username_input.send_keys("my702@naver.com")

    # password 입력
    password_input = driver.find_element_by_css_selector('#pass')
    password_input.send_keys("fblack9057") 
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
    print(a)

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


#텔레그램 챗봇
token = '2015300103:AAFDieSY7jKQ5ouXSi4agzmEq6Vc7CRCkAU'
# id = "2001756271"
 
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
            print(company)
            a = []
            for i in range(int(count)):
                a.append(company[i][0])
                print('a->',a)
                jobplanet(company,company[i][0], i)
                print('company->', company[i])
                data = extract_mail(company[i])
                bot.send_message(chat_id=id, text=data)
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



# In[ ]:
