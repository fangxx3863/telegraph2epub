# telegraph2epub

下载telegraph的内容至epub

# 使用方法

安装依赖
`pip3 install -r requirement.txt`

运行程序
`python3 telegraph2epub.py -u <URL>`

# 帮助内容

```
telegraph2epub [-h] [-v version] [-f folder] [-u url] [-j jobs]
    -h              显示帮助
    -v version      显示版本
    -f folder       指定下载路径
    -u url          下载链接
    -j jobs         下载线程
    Warning:        下载过程中会创建file目录以存放临时文件,请保证运行目录下无同名文件或文件夹
    Example:        telegraph2epub -u https://telegra.ph/xxx -j 32 -f book
    About:          https://github.com/fangxx3863/telegraph2epub
    Version:        v1.0
    ReleaseTime:    2021/12/19 13:30 PM
```
