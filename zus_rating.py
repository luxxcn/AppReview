import urllib2, json, xmltodict
from io import StringIO
import csv, codecs, requests
import string, time, operator

def getRatingsFromUrl(url):
	pageSum = 1
	page = pageSum
	response = urllib2.urlopen(url)
	j = xmltodict.parse(response.read())
	data = json.dumps(j)
	response.close() 
	d = json.loads(data)

	feed = d.get("feed")
	links = feed.get("link")

	reviews = []

	for link in links:
		rel = link.get("@rel")
		if rel == "last":
			lastLink = link.get("@href")

			if lastLink == "":
				return

			pageIndex = lastLink.find("page=") + 5
			lastPageNumber = int(lastLink[pageIndex])
			pageSum = lastPageNumber

	index = 0

	for p in range(1, (pageSum + 1)):
		newUrl = string.replace(url, 'customerreviews/', 'customerreviews/page=' + str(p) + '/')
		print newUrl
		response = urllib2.urlopen(newUrl)
		j = xmltodict.parse(response.read())
		data = json.dumps(j)
		response.close() 
		d = json.loads(data)

		feed = d.get("feed")
		entrys = feed.get("entry")

		for entry in entrys:
			updateAt = entry.get("updated")

			if updateAt < "2016-10-01T00:00:00-07:00": 
				continue

			rating = entry.get("im:rating")
			if rating == None:
				continue

			version = entry.get("im:version")
			title = entry.get("title")
			content = entry.get("content")[0].get("#text")
			author = entry.get("author").get("name")

			if rating != None:
				index = index + 1
				# print str(index) + ": " + updateAt + " --- " + rating + " --- " + version + " --- " + author + " --- " + title + " --- " + content
				review = [updateAt, rating, version, author, title, content]
				reviews.append(review)

	return reviews

def getRatingsFromCountry(country):
	url = "https://itunes.apple.com/" + country + "/rss/customerreviews/id=1038723291/sortby=mostrecent/xml"
	return getRatingsFromUrl(url)

def getContryList(): 
	f = open("country_list", 'r')

	country_list = []
	for line in f:
		country_list.append(line[:-1])

	return country_list

def send_email(rating, count):
	today = time.strftime('_%Y_%m_%d',time.localtime(time.time()))
	attachmentFile = "zus_q4_ios_review" + today + ".csv"

	f = open('mailKey', 'r')
	keys = []
	for line in f:
		keys.append(line[:-1])

	return requests.post(
        "https://api.mailgun.net/v3/" + keys[0] + "/messages",
        auth=("api", keys[1]),
        files=[("attachment", open(attachmentFile))],
        data={"from": "ZUS iOS Rating Team <dongdong@nonda.us>",
              "to": ["zus-dev@nonda.us"],
              "subject": "Daily Report - ZUS App iOS Rating - " + str(rating) + "/4.5(" + str(int(count)) + ")",
              "text": "Rating: " + str(rating) + "/4.5(" + str(int(count)) + ")" })

def get_today_reviews():
	countries = getContryList()
	reviews = []

	for c in countries: 	
	 	reviewsCountry = getRatingsFromCountry(c)
	 	if reviewsCountry == None:
	 		continue

		for review in reviewsCountry:
			review.insert(0, c)
			reviews.append(review)

	return reviews

def sort_reviews(lists):
	return sorted(lists, key=lambda x: x[1])

newList = sort_reviews(get_today_reviews())[::-1]
today = time.strftime('_%Y_%m_%d',time.localtime(time.time()))
csvfile = file('zus_q4_ios_review' + today + '.csv', 'wb')
csvfile.write(codecs.BOM_UTF8)
writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
writer.writerow(['Country', 'Date', 'Rating', 'Version', 'Name', 'Title', 'Content'])

ratingSum = 0.0
ratingCount = 0.0
for review in newList:
	ratingSum = ratingSum + int(review[2])
	ratingCount = ratingCount + 1
	writer.writerow([unicode(s).encode("utf-8") for s in review])

averageRating = round(ratingSum/ratingCount, 1)
writer.writerow(['', '', str(averageRating)])
csvfile.close()

print averageRating, ratingCount
print send_email(averageRating, ratingCount)
