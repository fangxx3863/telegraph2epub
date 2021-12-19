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
import getopt
import zipfile
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
        
    

def writeToBook(title, author, content, cover_name, cover_file, imgDir, folder=None):
    """写入内容至epub

    传入基本参数，并将其写出至epub

    Args:
        title (str): 书籍名称
        author (str): 作者名称
        content (str): 文章html内容
        cover_name (str): 封面名称
        cover_file (str): 封面路径
        imgDir (str): 引用图片路径
    """    
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(title)
    book.set_language('zh')
    book.add_author(author)
    cover_type = cover_file.split('.')[-1]
    book.set_cover(cover_name + '.' + cover_type, open(cover_file, 'rb').read())
    c1 = epub.EpubHtml(title=title,
                       file_name='content.xhtml',
                       lang='zh')
    content = content.replace('png', 'jpg')
    
    # 添加CSS规则
    css = '<style>img {text-align: center !important; text-indent: 0px !important; display: block !important; width: 100% !important}</style>'
    content = str(content)[1:-1]
    content = content + css
    #print(content)
    
    c1.set_content(content)
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

    '''
    # 添加CSS样式
    style = 'body {position: absolute; width: auto; height: 100%; margin: auto; text-align:center;}'
    content_css = epub.EpubItem(uid="style_content", file_name="style/content.css", media_type="text/css", content=style)
    book.add_item(content_css)
    '''

    if folder is None:
        folder = ''
    else:
        isExists=os.path.exists(folder) #判断路径是否存在
        if not isExists:
            # 如果不存在则创建目录
            os.makedirs(folder)
        folder = str(folder) + '/'
    
    epub.write_epub(folder + title + '.epub', book)
    
def getPage(url, ):
    info = {'status': '', 'title': '', 'author': '', 'imgUrls': '', 'content': '', 'cover_file': ''}
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
    info['cover_file'] = re.search('<img[^>]*>', content).group()[10:-3]
    
    return info
    
def downloadImage(url, jobs):
    imgUrls = getPage(url)['imgUrls']
    pool = Pool(int(jobs))
    errUrls = pool.map(downloadFile, imgUrls)
    errUrls = sorted(list(filter(None, errUrls)))
    while errUrls:
        errUrls = downloadFile(errUrls)
    #print(errUrls)
    

def zipDir(dirpath, outFullName):
    zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath, '')
 
        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()


def main():
    opts,args = getopt.getopt(sys.argv[1:],'-h-f:-v-u:-j:-c',['help','folder=','version','url=','jobs=','cbz'])
    jobs = 8
    folder = None
    cbz = False
    for opt_name,opt_value in opts:
        if opt_name in ('-h','--help'):
            help_str = '''
将telegraph的漫画或文章下载为epub文件

telegraph2epub [-h help] [-v version] [-f folder] [-u url] [-j jobs] [-c cbz]
    -h help         显示帮助
    -v version      显示版本
    -f folder       指定下载路径
    -u url          下载链接
    -c cbz          以cbz方式存储所有图像
    -j jobs         下载线程
    Warning:        下载过程中会创建file目录以存放临时文件,请保证运行目录下无同名文件或文件夹
    Example:        telegraph2epub -u https://telegra.ph/xxx -j 32 -f book
    About:          https://github.com/fangxx3863/telegraph2epub
    Version:        v1.0
    ReleaseTime:    2021/12/19 13:30 PM
                      '''
            print(help_str)
            exit()
            
        if opt_name in ('-v','--version'):
            print("Version is v1.0 ")
            exit()
            
        if opt_name in ('-f','--folder'):
            folder = opt_value
            
        if opt_name in ('-u', '--url'):
            url = opt_value
            
        if opt_name in ('-j', '--jobs'):
            jobs = opt_value
        
        if opt_name in ('-c', '--cbz'):
            cbz = True
    
    try:
        downloadImage(url, jobs)
        Page = getPage(url)
    except:
        print('你未输入URL,加入-h参数显示帮助!')
        exit()
        
    if cbz is False:
        try:
            writeToBook(Page['title'], Page['author'], Page['content'], 'cover', Page['cover_file'], 'file', folder)
            shutil.rmtree('file')
        except:
            print('写入文件错误!')
            exit()
    else:
        p = 0
        for i in Page['imgUrls']:
            p += 1
            path = str(i)[19:]
            filetype = path.split('.')[-1]
            os.rename(path, 'file/' + str(p) + '.' + filetype)
            
        if folder is None:
            folder = ''
        else:
            isExists=os.path.exists(folder) #判断路径是否存在
            if not isExists:
                # 如果不存在则创建目录
                os.makedirs(folder)
            folder = str(folder) + '/'
        zipDir('file', folder + Page['title'] + '.cbz')
        shutil.rmtree('file')
        
    

if __name__ == "__main__":
    main()