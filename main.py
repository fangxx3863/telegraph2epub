import ebooklib
from ebooklib import epub
import uuid
import requests
from bs4 import BeautifulSoup as bs
import download
from download import download
import os
import ssl
import sys
import re
from PIL import Image
import shutil
import io
import time
from multiprocessing import Process, Pool


# 关闭SSL证书验证
ssl._create_default_https_context = ssl._create_unverified_context

# 初始化epub工具
book = epub.EpubBook()

# 下载函数
def downloadFile(url, path='file'):
    if isinstance(url, str):
        try:
            download(url, os.getcwd() + '/' + str(path) + '/' + os.path.basename(url), replace=False, verbose=False)
        except:
            return url
    if isinstance(url, list):
        errUrls = []
        for i in url:
            try:
                download(i, os.getcwd() + '/' + str(path) + '/' + os.path.basename(i), replace=False, verbose=False)
            except:
                errUrls.append(i)
                return errUrls
        
    

def writeToBook(title, author, content, coverName, coverFile, imgDir):
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(title)
    book.set_language('zh')
    book.add_author(author)
    book.set_cover(coverName, open(coverFile, 'rb').read())
    c1 = epub.EpubHtml(title=title,
                       file_name='content.xhtml',
                       lang='zh')
    content = content.replace('png', 'jpg')
    c1.set_content(str(content)[1:-1])
    book.add_item(c1)
    book.toc = ((c1, )  # 添加c1到目录
                )
    imgDirList = os.listdir(imgDir)
    for filename in imgDirList:
        filetype = filename.split('.')[-1]

        # 加载图片文件
        img = Image.open(imgDir + '/' + filename)  # 'image1.jpeg' should locate in current directory for this example
        b = io.BytesIO()
        img = img.convert('RGB')
        img.save(b, 'jpeg')
        data_img = b.getvalue()

        filename = filename.replace('png', 'jpg')
        img = epub.EpubItem(file_name="file/%s" % filename,
                            media_type="image/jpeg", content=data_img)
        book.add_item(img)
    
    # basic spine
    book.spine = [c1, ]

    # 添加CSS样式
    style = 'body {position: absolute; width: auto; height: 100%; margin: auto; text-align:center;}'
    content_css = epub.EpubItem(uid="style_content", file_name="style/content.css", media_type="text/css", content=style)
    book.add_item(content_css)

    epub.write_epub(title + '.epub', book)
    
def getPage(url, ):
    info = {'status': '', 'title': '', 'author': '', 'imgUrls': '', 'content': '', 'coverFile': ''}
    page = requests.get(url)
    info['status'] = page.status_code
    print('Get Code:', page.status_code)
    
    # 初始化soup解析html
    soup = bs(page.text, "html.parser")
    
    # 解析标题
    title = str(soup.find('title').string)
    info['title'] = title
    print('Title:', title)
    
    # 解析作者
    author = str(soup.find('a', {'rel': 'author'}).string)
    info['author'] = author
    print('Author:', author)
    
    # 解析图片链接
    imgUrls = []
    images = soup.findAll('img')
    for i in range(0, len(images)):
        img = "https://telegra.ph" + str(images[i])[10:-3]
        imgUrls.append(img)
    info['imgUrls'] = imgUrls
    #print(imgUrls)
    
    # 解析正文内容
    content = str(soup.find_all(name='article', attrs={'class': 'tl_article_content'}))
    # 替换一些内容
    content = content.replace('/file', 'file')
    content = content.replace('/article', '/body')
    content = re.sub('<article*(.+?)>', '', content)
    content = content.replace('</article>', '')
    content = re.sub('<address><a.*</address>', '', content)
    content = content.replace('</body>', '')
    info['content'] = content
    #print(content)
    
    # 封面图文件名
    info['coverFile'] = re.search('<img[^>]*>', content).group()[10:-3]
    
    return info
    
def downloadImage(url):
    imgUrls = getPage(url)['imgUrls']
    pool = Pool(8)
    errUrls = pool.map(downloadFile, imgUrls)
    errUrls = sorted(list(filter(None, errUrls)))
    while errUrls:
        errUrls = downloadFile(errUrls)
    #print(errUrls)
    
if __name__ == "__main__":
    try:
        url = sys.argv[1]
        downloadImage(url)
        Page = getPage(url)
    except:
        print('你未输入URL！')
        
    try:
        writeToBook(Page['title'], Page['author'], Page['content'], Page['title'], Page['coverFile'], 'file')
        shutil.rmtree('file')
    except:
        print('写入文件错误！')
        exit(0)