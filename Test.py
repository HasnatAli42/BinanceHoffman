from array import array
from datetime import datetime

string = str(datetime.now())
print(string)
list = []
list.append(1)
list.append(1.1452542525254354354353532525)
list.append(1.1)
list.append(0.9)
list.append(0.9)
list.append(1)
list.append(1.1)
list.append(1.1)
list.append(0.9)
list.append(1)
list.append(1.1)
list.append(1.1)
list.append(1.1)
list.append(1.1)
list.append(1.1)
list.append(1.1)
list.append(0.9)
list.append(0.9)
list.append(0.9)
list.append(0.9)
list.append(0.9)
list.append(0.9)
list.append(0.9)
list.append(0.9)
list.append(0.9)
list.append(0.9)
list.append(10)

def straight_line_check(ema_positive_list):
    # sum = 0
    # for element in ema_positive_list:
    #     element = float(element)
    #     sum = sum + element
    average = sum(ema_positive_list) / len(ema_positive_list)
    counter = 0
    for element in ema_positive_list:
        counter += 1
        if -0.25 <= average - element <= 0.25:
            pass
        else:
            break
    if counter < len(ema_positive_list):
        del ema_positive_list[0:counter]
        return False
    else:
        return True

print(list)
print(len(list))
print(straight_line_check(list))
print(list)
print(len(list))











# print(list)
# sum = 0
# for x in list:
#     x = float(x)
#     sum = sum + x
# average = sum / len(list)
# print("Sum", sum)
# print("Average", average)
# counter = 0
# for x in list:
#     counter += 1
#     if -0.12 <= average - x <= 0.12:
#         print("1.Value Good",average - x)
#     else:
#         print("Value Not Good",average - x)
#         break
# print("counter = ",counter," list_length = ",len(list))
# if counter < len(list):
#     del list[0:counter]
#     print("Not a Straight Line")
# else:
#     print("It is a Straight Line")
# print("list_length_after_deleting = ",len(list))
# print(list)


