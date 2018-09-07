from ebooklib import epub
from urllib import request
from fake_useragent import UserAgent
import http.client 
import re
http.client._MAXHEADERS = 1000

# Read first page
#link = "https://royalroadl.com/fiction/8894/everybody-loves-large-chests/chapter/99919/prologue"
#link = "https://royalroadl.com/fiction/5701/savage-divinity/chapter/58095/chapter-1-new-beginnings"
link = input("Give webside of the first chapter: ")
ua = UserAgent()
req = request.Request(link)
req.add_header('User-Agent', ua.chrome)
webpage = request.urlopen(req).read().decode('utf-8')
webpage = re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\U00010000-\U0010FFFF]+', '', webpage)
webpage = re.sub(' +',' ',webpage)
titleIndex = webpage.find("keywords")
newTitleIndex = webpage.find("=",titleIndex)+2
endOfTitle = webpage.find(";",newTitleIndex)
while True:
	if(webpage[endOfTitle-4] == "&"):
		endOfTitle = webpage.find(";",endOfTitle+1)
	else:
		break
endOfAuthor = webpage.find(";",endOfTitle+1)
while True:
	if(webpage[endOfAuthor-4] == "&"):
		endOfAuthor = webpage.find(";",endOfAuthor+1)
	else:
		break
BookTitle = webpage[newTitleIndex:endOfTitle]
Author = webpage[endOfTitle+1:endOfAuthor]
image_url_start = webpage.find("=",webpage.find("og:image"))+2
image_url_end = webpage.find(">",image_url_start)-1
image_url = webpage[image_url_start:image_url_end]
image = request.urlopen(image_url).read()

print("Book Title:")
print("\t" + BookTitle)
print("Author:")
print("\t" + Author)

book = epub.EpubBook()
book.set_identifier(Author + BookTitle)
book.set_title(BookTitle)
book.set_language('en')
book.add_author(Author)
book.set_cover("cover.jpg", image)

# define CSS style
style_url_begin = webpage.find("href", webpage.find("stylesheet"))+6
style_url_begin = webpage.find("href", webpage.find("stylesheet",style_url_begin+5))+6
style_url_end = webpage.find(">",style_url_begin)-2
style_url = "https://royalroadl.com" + webpage[style_url_begin:style_url_end]
req = request.Request(style_url)
req.add_header('User-Agent', ua.chrome)
style = request.urlopen(req).read().decode()
nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)

# add CSS file
book.add_item(nav_css)
# add spine
book.spine = ['cover','nav']
chapterCount = 1

while True:
	# Fix some lxml error
	webpage = re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\U00010000-\U0010FFFF]+', '', webpage)
	# find chapter title
	beginOfAuthor = webpage.find(Author)
	endOfAuthor = webpage.find(";",beginOfAuthor)
	endOfChTitle = webpage.find("; free",endOfAuthor+1)
	ChaperTitle = webpage[endOfAuthor+1:endOfChTitle]
	try:
		print("Chapter Title " +str(chapterCount).zfill(3)+":\t" + ChaperTitle)
	except UnicodeEncodeError:
		print(("Chapter Title " +str(chapterCount).zfill(3)+":\t" + ChaperTitle).encode('utf-8'))
	# create chapter
	chapter = epub.EpubHtml(title=ChaperTitle, file_name= str(chapterCount).zfill(3) +".xhtml", lang='en')
	chapter.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
	beginOfChapter = webpage.find(r"<div",webpage.find("chapter-inner chapter-content")-20)
	divs = 1
	lastDiv = beginOfChapter+5
	while divs > 0:
		nextDiv = webpage.find("div",lastDiv)
		if webpage[nextDiv-1:nextDiv] == "<":
			divs += 1
		elif webpage[nextDiv-1:nextDiv] == "/":
			divs -= 1
		# else:
			# not a command, just ignore
		lastDiv = nextDiv + 1
	endOfChapter = lastDiv + 3
	chapter.content = "<h1>"+ ChaperTitle +"</h1>" + webpage[beginOfChapter:endOfChapter]

	# add chapter
	book.add_item(chapter)
	book.spine += [chapter]
	book.toc += [chapter]

	# check if next chapter is available
	if webpage.find("disabled", webpage.find("Index", endOfChapter), webpage.find("Index", endOfChapter) + 800) != -1:
		break
	chapterCount += 1

	# Find next chapter link
	beginNextChLink = webpage.find("href=", webpage.find("Index", endOfChapter))+6
	endNextChLink = webpage.find(">Next",beginNextChLink)-1
	NextChLink = "https://royalroadl.com" + webpage[beginNextChLink:endNextChLink]
	# Load next chapter webpage
	req = request.Request(NextChLink)
	req.add_header('User-Agent', ua.chrome)
	webpage = request.urlopen(req).read().decode('utf-8')
	

# add default NCX and Nav file
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())
# write to the file
BookTitle = re.sub('[\\/:"*?<>|]+', '', BookTitle)
epub.write_epub(BookTitle + ".epub", book, {})

print("End of Program")