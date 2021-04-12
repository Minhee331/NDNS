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

# idx = 0
# naverUrls = []
# urls = []

def lambda_handler(event, context):
    idx = 0
    naverUrls = []
    urls = []
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
                    p = re.compile('se-fs-')
                    title = html.find('span', {'class':p}).get_text()
                    # body 추출
                    body = html.find('div', {'class':'se-main-container'}).get_text()
                    body = re.compile('[^가-힣0-9ㄱ-ㅎㅏ-ㅣa-zA-Z.^]+').sub(' ', body).strip()
                    # imgURL 추출
                    imgUrlL = []
                    for imgUrl in html.find_all('img', {'class': 'se-image-resource'}):
                        imgUrl = imgUrl.get('src')
                        imgUrl = imgUrl.replace('w80_blur', 'w800')
                        #imgURL List 에 하나씩 추가
                        imgUrlL.append(imgUrl)
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
                        body = html.find('div', {'class':'post_ct'}).get_text()
                        body = re.compile('[^가-힣0-9ㄱ-ㅎㅏ-ㅣa-zA-Z.^]+').sub(' ', body).strip()
    
                        # imgURL 추출
                        imgUrlL = []
                        i = re.compile('_img')
                        for imgUrl in html.find_all('span', {'class':i}):
                            imgUrl = imgUrl.get('thumburl')
                            imgUrlL.append(imgUrl+'w2')
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
                                body += re.compile('[^가-힣0-9ㄱ-ㅎㅏ-ㅣa-zA-Z.^]+').sub(' ', bitem).strip()
                            # imgURL 추출
                            imgUrlL = []
                            i = re.compile('se_mediaImage')
                            for imgUrl in html.find_all('img', {'class':i}):
                                imgUrl = imgUrl.get('src')
                                imgUrl = imgUrl.replace('w80_blur', 'w800')
                                imgUrlL.append(imgUrl)
                            review["title"] = title
                            review["body"] = body
                            review["imgUrl"] = imgUrlL 
                        
                            conn.send(review)
                            conn.close()  
                        except:
                            del review
                            return 2
            else :
                res = requests.get(url) 
                html = res.text
                soup = BeautifulSoup(html,'html.parser')
    
                if(soup.find("div", {"class": "hgroup"}) != None):
                    title = soup.find("div", {"class": "hgroup"})
                elif(soup.find("div", {"class": "box-meta"}) != None):
                    title = soup.find("div", {"class": "box-meta"})
                elif(soup.find("div", {"class": "area_title"})!= None):
                    title = soup.find("div", {"class": "area_title"})
                elif(soup.find("div", {"class": "inner"})!= None):
                    title = soup.find("div", {"class": "inner"})
                elif(soup.find("div", {"class": "jb-content-title jb-content-title-article"})!= None):
                    title = soup.find("div", {"class": "jb-content-title jb-content-title-article"})
                elif(soup.find("div", {"id": "head"})!= None):
                    title = soup.find("div", {"id": "head"})
                else:
                    title = None
                
                if title is not None:
                    if(title.find({"class": "title-article"}) is not None):
                        title_text = title.find({"class": "title-article"})
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
                
                if result != '':
                    ptags = ''
                    for i in result.find_all('p'):
                        if len(i.get_text(strip=True)) != 0 and i.string is not None:
                            # ptags.append(i.string)
                            ptags = ptags + i.string + ''
                    img = list()
                    for i in result.find_all("img"):
                        img.append(i.get('src'))
                    review["title"] = title_text.get_text()
                    review["body"] = ptags
                    review["imgUrl"] = img
                
                    conn.send(review)
                    conn.close()    
        except:
            pass

    __name__ = '__main__'
    if __name__ == '__main__' :
        reviews = []
    
        # 검색어
        inputValue = "칫솔 살균기"
        inputValue = inputValue.replace(' ', '+' )
    
        # 네이버 검색창 크롤링
        NSearchUrl = 'https://search.naver.com/search.naver?query='+inputValue+'&where=blog&sm=tab_viw.all'
    
        response = requests.get(NSearchUrl)
    
        if response.status_code == 200 :
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            soup = soup.find(id='main_pack').find_all('a',{'class': 'api_txt_lines total_tit'})
            for link in soup :
                if 'naver' not in link['href']:
                    continue
                idx += 1
                review = {'id' : idx, 'linkUrl' : link['href'], 'source' : 'N'}
                naverUrls.append(link['href'])
                reviews.append(review)
        else :
            return {
            'status_code' : response.status_code,
            'body' : 'error'
            }
    
        # 구글 검색창 크롤링
        if (inputValue.find('리뷰') != -1 or inputValue.find('후기') != -1):
            GSearchUrl = 'https://www.google.com/search?q='+inputValue+'&sourceid=chrome&ie=UTF-8'
        else:
            GSearchUrl = 'https://www.google.com/search?q='+inputValue+'+리뷰'+'&sourceid=chrome&ie=UTF-8&start=0'
    
        pages = 0
        while(len(reviews) <= 50):    
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
                        if 'naver' in url: 
                            url = url.replace('/m.','/')
                            if not url in naverUrls :
                                idx += 1
                                review = {'id' : idx, 'linkUrl' : url, 'source' : 'G'}
                                reviews.append(review)
                        elif 'tistory' in url :
                            idx += 1
                            review = {'id' : idx, 'linkUrl' : url, 'source' : 'G'}
                            reviews.append(review)
                    except :
                        pass
            else :
                break
    
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
            
        for parent_connection in parent_connections:
            review = parent_connection.recv()
            reviews[review["id"] - 1] = review
        
        
        bucket_name = "awstest123"
        file_name = "test.txt"
        s3_path = "test/2/" + file_name
        
        s3 = boto3.resource(
            's3',
            region_name='ap-northeast-2',
            aws_access_key_id='AWS_ID',
            aws_secret_access_key='AWS_PASSWORD'
        )
        s3.Object(bucket_name, s3_path).put(Body=json.dumps(reviews))
        
        obj = s3.Object(bucket_name, s3_path)
        body = obj.get()['Body'].read()
        
        return body