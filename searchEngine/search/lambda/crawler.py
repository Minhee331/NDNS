import requests
from bs4 import BeautifulSoup
import functools
import multiprocessing
import re  # 정규표현식
import json # json
import sys
import boto3

# 참고 naver 검색어 parsing https://brownbears.tistory.com/501
# beautifulsoup https://wikidocs.net/85739

def lambda_handler(event, context):
    idx = 0
    naverUrls = []
    urls = []

    check = False

    def checkad(body):
        if '제공' in body or '지원' in body or '협찬' in body or '지급' in body:
            if '받아' in body or '받았' in body or '제공받아' in body or '지원받아' in body or '제품' in body:
                return True
            elif '않' in body:
                return False
            else:
                return False
        if '원고료' in body or '제작비' in body or '수수료' in body or '수익금' in body or '수익금이' in body:
            if '소정' in body or '지원' in body or '받아' in body or '발생' in body or '발생할' in body or '지급' in body or '지원받아' in body or '지급받아' in body or '파트너스' in body:
                return True
            else:
                return False
        else:
            return False
    
    def select(conn, review):
        try:
            url = review['linkUrl']
            if 'naver' in url:
                url = url.replace('https://', 'https://m.')
                url = url.replace('http://', 'https://m.')
                res = requests.get(url)
                text = res.text
                html = BeautifulSoup(text, 'html.parser')
                try:
                    # title 추출
                    p = re.compile('se-title-text')
                    title = html.find('div', {'class':p}).get_text()
                    # body 추출
                    body = ""
                    for bitem in html.find_all('div', {'class':'se-section-text'}):
                        bitem = bitem.get_text()
                        if bitem == "" or bitem == " ":
                            continue
                        body = body + re.compile('[^가-힣0-9ㄱ-ㅎㅏ-ㅣa-zA-Z.^]+').sub(' ', bitem).strip() + ". "
                    # imgURL 추출
                    imgUrlL = []
                    for imgUrl in html.find_all('img', {'class': 'se-image-resource'}):
                        imgUrl = imgUrl.get('src')
                        imgUrl = imgUrl.replace('w80_blur', 'w800')
                        #imgURL List 에 하나씩 추가
                        imgUrlL.append(imgUrl)
                    #check ad
                    for i in body.split('.'):
                        check = checkad(i)
                        if check == True:
                            break

                    review["isAd"] = check
                    review["title"] = title
                    review["body"] = body
                    review["imgUrl"] = imgUrlL 
                    conn.send(review)
                    conn.close() 
                except:
                    try:
                        # title 추출
                        h = re.compile('tit_')
                        title = html.find('h3', {'class':h}).get_text()
    
                        # body 추출
                        body = ''
                        for bitem in html.find_all('p', attrs = {'align':'center'}):
                            bitem = bitem.get_text()
                            if bitem == "" or bitem == " ":
                                continue
                            body = body + re.compile('[^가-힣0-9ㄱ-ㅎㅏ-ㅣa-zA-Z.^]+').sub(' ', bitem).strip() + ". "
    
                        # imgURL 추출
                        imgUrlL = []
                        i = re.compile('_img')
                        for imgUrl in html.find_all('span', {'class':i}):
                            imgUrl = imgUrl.get('thumburl')
                            imgUrlL.append(imgUrl+'w2')

         #check ad
                        for i in body.split('.'):
                            check = checkad(i)
                            if check == True:
                                break

                        review["isAd"] = check                            
                        review["title"] = title
                        review["body"] = body
                        review["imgUrl"] = imgUrlL 
                    
                        conn.send(review)
                        conn.close() 
                    except:  
                        try:
                            # title 추출
                            h = re.compile('se_textarea')
                            title = html.find('h3', {'class':h}).get_text()
                            # body 추출
                            body = ''
                            for item in html.find_all('p', {'class':'se_textarea'}):
                                bitem = item.get_text()
                                if bitem == "" or bitem == " ":
                                    continue
                                body = body + re.compile('[^가-힣0-9ㄱ-ㅎㅏ-ㅣa-zA-Z.^]+').sub(' ', bitem).strip() + ". "
                            # imgURL 추출
                            imgUrlL = []
                            i = re.compile('se_mediaImage')
                            for imgUrl in html.find_all('img', {'class':i}):
                                imgUrl = imgUrl.get('src')
                                imgUrl = imgUrl.replace('w80_blur', 'w800')
                                imgUrlL.append(imgUrl)


                            #check ad
                            for i in body.split('.'):
                                check = checkad(i)
                                if check == True:
                                    break

                            review["isAd"] = check    
                            review["title"] = title
                            review["body"] = body
                            review["imgUrl"] = imgUrlL 
                        
                            conn.send(review)
                            conn.close()  
                        except:
                            review["fail"] = 1
                            conn.send(review)
                            conn.close()  
                        
            else :#tistory
                res = requests.get(url) 
                html = res.text
                soup = BeautifulSoup(html,'html.parser')
    
                if(soup.find("div", {"class": "hgroup"}) != None):
                    title = soup.find("div", {"class": "hgroup"})
                elif(soup.find("div", {"class": "box-meta"}) != None):
                    title = soup.find("div", {"class": "box-meta"})
                elif(soup.find("div", {"class": "area_title"})!= None):
                    title = soup.find("div", {"class": "area_title"})
                elif(soup.find("div", {"class": "post-cover"})!= None):
                    title = soup.find("div", {"class": "post-cover"})
                elif(soup.find("div", {"class": "jb-content-title jb-content-title-article"})!= None):
                    title = soup.find("div", {"class": "jb-content-title jb-content-title-article"})
                elif(soup.find("div", {"class": "titleWrap"})!= None):
                    title = soup.find("div", {"class": "titleWrap"})
                elif(soup.find("div", {"class": "box_article_tit"})!= None):
                    title = soup.find("div", {"class": "box_article_tit"})
                elif(soup.find("div", {"class": "hd-inner"})!= None):
                    title = soup.find("div", {"class": "hd-inner"})
                elif(soup.find("div", {"class": "area_article"})!= None):
                    title = soup.find("div", {"class": "area_article"})
                elif(soup.find("div", {"class": "article_content"})!= None):
                    title = soup.find("div", {"class": "article_content"})
                elif(soup.find("div", {"id": "head"})!= None):
                    title = soup.find("div", {"id": "head"})
                else:
                    title = None
                
                if title is not None:
                    if(title.find({"class": "title-article"}) is not None):
                        title_text = title.find({"class": "title-article"})
                    elif(title.find({"class":"inner"})is not None):
                        title = title.find({"class":"inner"})
                        title_text = title.find('h1')
                    elif(title.find("p", {"class":"txt_sub_tit"})is not None):
                        title_text = title.find("p", {"class":"txt_sub_tit"})
                    elif(title.find("div", {"class":"title_view"})is not None):
                        title_text = title.find("a")
                    elif(title.find("strong",{"class": "title_post"})is not None):
                        title_text = title.find("strong",{"class": "title_post"})
                    elif(title.find('h1') is not None):
                        title_text = title.find('h1')
                    elif(title.find('h2') is not None):
                        title_text = title.find('h2')
                    elif(title.find('h3') is not None):
                        title_text = title.find('h3')
                    else:
                        title_text= "unable"
                else:
                    title_text= "unable"
    
                result=''
                if(soup.find("div", {"class": "tt_article_useless_p_margin"}) != None): #t1 &t2 공통 
                    result = soup.find("div", {"class": "tt_article_useless_p_margin"})
                elif(soup.find("div", {"class": "entry-content"})!= None):  #다른 스킨
                    result = soup.find("div", {"class": "entry-content"})
                elif(soup.find("div", {"class": "article"})!= None):  #다른 스킨
                    result = soup.find("div", {"class": "article"})
                elif(soup.find("div", {"class": "contents_style"})!= None):  #다른 스킨
                    result = soup.find("div", {"class": "contents_style"})
                else:
                    result = ''
    
                
                if result != '':
                    body = ''
                    for i in result.find_all('p'):
                        if len(i.get_text(strip=True)) != 0:
                            body = body + i.get_text(strip=True) + '.'
                        
                    # if body == '' and result.find("div", {"class": "contents_style"})!= None:
                    #     content = result.find("div", {"class": "contents_style"})
                    #     body = content.get_text()
                    if body == '' and result.find_all("span")!= None:
                        for i in result.find_all("span"):
                            body = body + i.get_text(strip=True) + '.'
                            
                    img = list()
                    for i in result.find_all("img"):
                        img.append(i.get('src'))
                        
                    #check ad
                    for i in body.split('.'):
                        check = checkad(i)
                        if check == True:
                            break

                    review["isAd"] = check
                    review["title"] = title_text.get_text()
                    review["body"] = body
                    review["imgUrl"] = img
                
                    conn.send(review)
                    conn.close()
                else:
                    review["fail"] = 1
                    conn.send(review)
                    conn.close()    
        except:
            review["fail"] = 1
            conn.send(review)
            conn.close()    

    __name__ = '__main__'
    if __name__ == '__main__' :
        try:
            params_arr = event['params']
            path_arr = params_arr['path']
            inputValue = str(path_arr['searchVal'])
        except Exception as e:
            return {"error": e}
        
        reviews = []
    
        # 검색어
        inputValue = inputValue.replace(' ', '+' )
    
        # 구글 검색창 크롤링
        if (inputValue.find('리뷰') != -1 or inputValue.find('후기') != -1):
            GSearchUrl = 'https://www.google.com/search?q='+inputValue+'&sourceid=chrome&ie=UTF-8'
        else:
            GSearchUrl = 'https://www.google.com/search?q='+inputValue+'+리뷰'+'&sourceid=chrome&ie=UTF-8&start=0'
    
        pages = 0
        while(len(reviews) <= 20):    
            GSearchUrl = GSearchUrl[:GSearchUrl.rfind('=') + 1]+ str(pages)
            pages += 10
            response = requests.get(GSearchUrl)
            
            if response.status_code == 200 :
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                soup = soup.find(id='main').find_all('div', {'class':'kCrYT'})
                
                if len(soup) == 1 :
                    break
                for link in soup :
                    try :
                        url = link.find('a')['href'][7:] 
                        url = url[:url.find('&')]
                        if (not 'tistory' in url) and (not 'naver' in url):
                            continue
                        elif 'naver' in url: 
                            nUrl = url.replace('https://', 'https://m.')
                            nUrl = url.replace('http://', 'https://m.')
                            naverUrls.append(nUrl)
                            # url = url.replace('/m.','/')
                            # if not url in naverUrls :
                            #     idx += 1
                            #     review = {'id' : idx, 'linkUrl' : url, 'source' : 'G'}
                            #     reviews.append(review)
                        # elif 'tistory' in url :
                        #     idx += 1
                        #     review = {'id' : idx, 'linkUrl' : url, 'source' : 'G'}
                        #     reviews.append(review)
                        idx += 1
                        review = {'id' : idx, 'linkUrl' : url, 'source' : 'G'}
                        reviews.append(review)    
                            
                    except :
                        pass
            else :
                break
        
        
        # 네이버 검색창 크롤링
        NSearchUrl = 'https://search.naver.com/search.naver?query='+inputValue+'&where=blog&sm=tab_viw.all'
    
        response = requests.get(NSearchUrl)
    
        if response.status_code == 200 :
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            soup = soup.find(id='main_pack').find_all('a',{'class': 'api_txt_lines total_tit'})
            for link in soup :
                url = link['href']
                if 'naver' not in url:
                    continue
                else:
                    nUrl = url.replace('https://', 'https://m.')
                    nUrl = url.replace('http://', 'https://m.')  
                    if nUrl in naverUrls :
                        continue
                idx += 1
                review = {'id' : idx, 'linkUrl' : url, 'source' : 'N'}
                reviews.append(review)
        else :
            return {
            'status_code' : response.status_code,
            'body' : 'error'
            }
    
        # return json.dumps(reviews, indent=2)
    
        processes = []
        parent_connections = []
        for idx in range(len(reviews)):
            # reviews[idx] = select(reviews[idx])
            # return select(reviews[idx])
            parent_conn, child_conn = multiprocessing.Pipe()
            parent_connections.append(parent_conn)
            
            process = multiprocessing.Process(target=select, args=(child_conn, reviews[idx]))
            processes.append(process)
            
        for process in processes:
            process.start()
            
        for process in processes:
            process.join()
        
        delList = []
        
        for parent_connection in parent_connections:
            review = parent_connection.recv()
            if "fail" in review :
                delList.append(review["id"])
            else:
                reviews[review["id"] - 1] = review
        
        delList.sort(reverse=True)
        
        for index in delList :
            del reviews[index - 1]
        
        
        return json.dumps(reviews, indent=2)