import re
import requests
import html5lib
from bs4 import BeautifulSoup
from numpy.core.defchararray import strip


# def sjf(jobs: list, index: int) -> int:
#     job = jobs[index]
#     valueGreater = 0
#     for index1 in range(index+1,len(jobs)):
#         if job == jobs[index1]:
#             valueGreater += 1
#     jobs.sort()
#     new_index= 0
#     for time in jobs:
#         if time==job:
#             required_index = new_index
#         new_index += 1
#
#     shortest_job = 0
#     for i in range (0 , required_index+1-valueGreater):
#         shortest_job = shortest_job + jobs[i]
#     return shortest_job
#
#
# print(sjf([10,10,10,10], 2))

def in_stock(title, topic):
    receivedTopic1 = ""
    url = "http://books.toscrape.com/index.html"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    table = soup.find('div', attrs={'class': 'side_categories'})
    isNextPage = True
    for row in table.findAll('a'):
        receivedTitle = str(strip(row.getText()))
        if receivedTitle.lower() == topic.lower():
            receivedLink = str(strip(row['href']))
            r = requests.get("http://books.toscrape.com/" + receivedLink)
            soup = BeautifulSoup(r.content, 'html.parser')
            for row in soup.findAll('a'):
                receivedTopic = str(strip(row.getText()))
                try:
                    receivedTopic1 = str(strip(row['title']))
                except:
                    pass
                if receivedTopic.lower() == "next":
                    current_link = str(strip(row['href']))
                    receivedLink = receivedLink.replace("index.html",current_link)
                    r = requests.get("http://books.toscrape.com/" + receivedLink)
                    soup = BeautifulSoup(r.content, 'html.parser')
                    for row in soup.findAll('a'):
                        receivedTopic = str(strip(row.getText()))
                        try:
                            receivedTopic1 = str(strip(row['title']))
                        except:
                            pass
                        if receivedTopic.lower() == "next":
                            while isNextPage:
                                counter = 0
                                new_link = str(strip(row['href']))
                                receivedLink = receivedLink.replace(current_link, new_link)
                                current_link = new_link
                                r = requests.get("http://books.toscrape.com/" + receivedLink)
                                soup = BeautifulSoup(r.content, 'html.parser')
                                for row in soup.findAll('a'):
                                    counter+=1
                                    # print(counter)
                                    receivedTopic = str(strip(row.getText()))
                                    try:
                                        receivedTopic1 = str(strip(row['title']))
                                    except:
                                        pass
                                    if receivedTopic.lower() == "next":
                                        break
                                    if receivedTopic.lower() != "next" and counter == 96:
                                        return False
                                    if receivedTopic.lower() == title.lower() or receivedTopic1.lower() == title.lower():
                                        return True
                        if receivedTopic.lower() == title.lower() or receivedTopic1.lower() == title.lower():
                            return True
                if receivedTopic.lower() == title.lower() or receivedTopic1.lower() == title.lower():
                    return True
    return False


print(in_stock("Grayson, Vol 3: Nemesis ...", "Sequential Art"))
