from base64 import b64decode
import random
import json
import requests
import time
import paho.mqtt.client as mqtt

def json_load_byteified(file_handle):
    return _byteify(
        json.load(file_handle, object_hook=_byteify),
        ignore_dicts=True
    )

def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )

def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data


###
host = "your.mqtt.service"
apiurl = "https://opentdb.com/api.php?amount=1&category=18"
topic = "/quiz"
###
correct_answer_index = 0
solved = 0

def mqprint(text):
	global client
	client.publish(topic, text)

def getquestion():

	global correct_answer_index

	r = requests.get(apiurl)
	data = json_loads_byteified(r.text)
	data = data["results"][0]
	#print(data)

	if(data["type"] == "boolean"):
		getquestion()
		return

	mqprint("Q: %s" % data["question"])
	mqprint("_"*len(data["question"]))

	correct = data["correct_answer"]
	incorrect = data["incorrect_answers"]

	answers = []
	for i in range(0,len(incorrect)):
		answers.append(incorrect[i])
	answers.append(correct)
	random.shuffle(answers)

	correct_answer_index = answers.index(correct)
	print("CAI: %i" % correct_answer_index)

	for i in range(0, len(incorrect)+1):
		mqprint("%i: %s" % (i, answers[i]))

def init():
	bytes = "\33[2J\n"
	with open("play.ascii","rb") as f:
		bytes += f.read()

	bytes += "\n"*3

	with open("howto.ansi","rb") as t:
		bytes += t.read()

	###
	client.publish(topic, bytes)
	getquestion()

def checkanswer(client, userdata, msg):
	global solved
	print("Got answer: %s" % msg.payload)
	if(int(msg.payload) == correct_answer_index):
		mqprint("%s is CORRECT!\n\n" % msg.payload)
		solved += 1
		if(solved % 5 == 0): init()
		else: getquestion()
	else:
		mqprint("%s is WRONG!" % msg.payload)

###
client = mqtt.Client()
client.connect(host, 1883, 60)
client.subscribe("/quiz/answer")
client.on_message = checkanswer
init()


client.loop_forever()
#client.start_loop()
