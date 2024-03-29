#importing modules
import json #for manipulating JSON files
import requests #for sending queries to ShanghAI (or Huggingface)
import discord #the Discord API
import os #for OS commands (like checking for files etc)
import sys #for system commands commands (like exit etc)
import re #regex module because for some reason pyshit doesn't come with it by default smh
from Naked.toolshed.shell import muterun_js #in order to run nodejs files from python
import time # for getting the current time

#import JSON(s)
#discord config file
if not os.path.isfile("./configs/bot_configs/discord.json"):
    sys.exit("'discord.json' not found! Please add it and try again.")
else:
    with open("./configs/bot_configs/discord.json") as file:
        config_d = json.load(file)

#model config file
if not os.path.isfile("./configs/model.json"):
    sys.exit("'model.json' not found! Please add it and try again.")
else:
    with open("./configs/model.json") as file:
        config_model = json.load(file)

#conversation history
if not os.path.isfile("./datasets/livedata.json"):
    sys.exit("'./dataset/livedata.json' not found! Please add it and try again.")
else:
    with open("./datasets/livedata.json") as file:
        convos = json.load(file)

#global vars
api_endpoint = "blep"
request_headers = "mlem"
ready = False

#define default emojis to be removed from the input text
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"
    "]+"
)

#define message sanitation
def sanitize_message(message):
    #check for comments
    ##if the message starts with this symbol, ignore it
    if message.startswith(config_d['PREFIX']):
        return False
    #clean up the user input
    ##remove some special emojis
    message = re.sub("<:.*:\d+>", "", message)
    ##remove the rest of the special emojis
    message = re.sub(":.*:", "", message)
    ##remove all default emojis
    message = re.sub(EMOJI_PATTERN, "", message)
    ##check for links and urls
    if re.findall("\A(http|www)", message):
        #remove said links until you reach a white space
        temp_msg = message.split(' ', 1)
        if (len(temp_msg)>1):
            message = message[1]
        else:
            message = ''
    #check for `?` message and replace it with `What?`
    if message == '?':
        message = 'What?'
    #check if there is some semblance of a word left
    if not re.findall("\w", message):
        #if message is emojos/links only, don't bother
        return False
    return message

#define the query function for ShanghAI
def query_ShanghAI(payload, api_endpoint, request_headers):
    #create the json file to be sent over
    data = json.dumps(payload)
    #make a POST request and store the response
    response = requests.request('POST', api_endpoint, headers=request_headers, data=data)
    #decode the content of the response (it's not a json here)
    ret = response.content.decode('utf-8')
    #return the decoded response
    return ret

#define the query function for the Hugginface API
def query_hf(payload, api_endpoint, request_headers):
    #create the json file to be sent over
    data = json.dumps(payload)
    #make a POST request and store the response
    response = requests.request('POST', api_endpoint, headers=request_headers, data=data)
    #decode the content of the response
    ret = json.loads(response.content.decode('utf-8'))
    #return the decoded response
    #if there are any errors, send them over to the terminal
    if "error" in ret:
        print(ret)
        #also, send them forwards anyway, so we may get the estimated time if possivle
        return ret
    #if there are no erros, return that sweet sweet ai generated text
    if "generated_text" in ret:
        return ret["generated_text"]

#function to give ShanghAI the compiled dataset
def send_dataset():
    #crete the file payload with the dataset.csv file
    files = {'file': ('dataset.csv', open('./datasets/dataset.csv', 'rb'),'text/csv')}
    #PUT request to ShanghAI's 'dataset_transfer' endpoint
    requests.put(config_d['ShanghAI-URL']+'dataset_transfer', headers={}, files=files, verify=False)

#define function that builds livedata.json from the conversations the bot has
#useful for retraining the model, or for logging
async def append_chat_history(user, line, reply):
    #create the username
    user = user.split("#")[0]
    #create the dialogue object
    convos[config_d['linenum']] = {
        "username": user,
        "userquote": line,
        "botreply": reply
    }
    #write dialogue to conversation file
    with open("./datasets/livedata.json", "w") as outfile:
        json.dump(convos, outfile)
    #increment line number
    config_d["linenum"] = config_d["linenum"] + 1
    #write new line number to config file
    with open("./configs/bot_configs/discord.json", "w") as outfile:
        json.dump(config_d, outfile)

#define the function that will add live data to the main dataset file
async def build_dataset():
    #run the data_parser.js script
    response = muterun_js('./data_parser.js')
    #check if it finished with no errors
    if response.exitcode == 0:
        #send dataset to ShanghAI for training
        send_dataset()
        #reset the convos object
        convos = {}
        #crete the backup file
        os.rename('./datasets/livedata.json','./datasets/livedata.{}.bk'.format(time.time()))
        #reset teh livedata.json file
        with open('./datasets/livedata.json','rw') as file:
            json.dump(convos, file)
            convos = json.load(file)
        #reset the linenum
        config_d["linenum"] = 0
        #write new line number to config file
        with open("./configs/bot_configs/discord.json", "w") as outfile:
            json.dump(config_d, outfile)
        #return the output of the script
        return response.stdout
    else:
        return response.stderr

#setup intents for the discord client
intents = discord.Intents.all()
#initialize the discord client with the intents
client = discord.Client(intents=intents)

#do when app starts
@client.event
async def on_ready():
    #global vars
    global api_endpoint, request_headers, ready
    #print out some console information when the bot starts
    print(client.user.name + ' starting up...')
    #check which platform the user wants to use
    #Hugginface (cloud) or ShanghAI (local)
    if config_d['ShanghAI']:
        #begin setting up for ShanghAI
        print('Attempting to handshake with ShanghAI...')
        #check if ShanghAI is up and running
        ##create the endpoint for ShanghAI's check() function
        api_endpoint = config_d['ShanghAI-URL'] + 'check'
        ##create headers for json data
        request_headers = {'content-type': "application/json", 'cache-control': "no-cache"}
        ##form the payload necessary to ShanghAI's check() function
        payload = {"check": "I should make this something else"}
        ##send the check request to see if ShanghAI is runnig
        response = query_ShanghAI(payload, api_endpoint, request_headers)
        #if ShanghAI is indeed up
        if response == 'check':
            #tell ShanghAI to load the AI model
            print('ShanghAI loading {} model...'.format(config_d['MODEL_NAME']))
            ##create link to ShanghAI's load() function
            api_endpoint = config_d['ShanghAI-URL'] + 'load'
            ##create headers for json data
            request_headers = {'content-type': "application/json", 'cache-control': "no-cache"}
            ##create the payload necessary for ShanghAI's load() function
            payload = {
                "model": "./" + config_d['MODEL_NAME'],
                "args": config_model['args']
                }
            #send the required data to ShanghAI so that sge begins loading the model
            response = query_ShanghAI(payload, api_endpoint, request_headers)
            #when ShanghAI is ready:
            ##print her response
            print(response)
            ##store ShanghAI's state in a boolean var
            ready = True
            ##log in the console that she was done downloading and/or loading the model
            print('ShanghAI finished loading {} model'.format(config_d['MODEL_NAME']))
        #if for some reason ShanghAI failed to connect to HourAI
        else:
            #TODO:
            print('Hanshake failed.')
    #if Hugginface is used
    elif config_d['Hugginface']:
        #begin setting up for Hugginface API
        ##create link to the API
        api_endpoint = config_d['HF-URL'] + config_d['MODEL_NAME']
        ##get the Hugginface token
        hf_token = config_d['HF-TOKEN']
        ##create the requests header
        request_headers = {
            'Authorization': 'Bearer {}'.format(hf_token)
        }
        #make a test query to wake the API up
        resp = query_hf({'inputs': {'text': 'Hello!'}}, api_endpoint, request_headers)
        #print the time it will take her to wake up
        if "estimated_time" in resp:
            print("Model loading... ETA: {}".format(resp["estimated_time"]))
    #if neither backend is specified uhhhhh
    else:
        #no API specified, please do that
        sys.exit("Please specify a platform in the 'configs/bot_configs/discord.json' file.")
    #console log that the bot has finished the setting up
    print(client.user.name + ' ready to go!')
    #set bot status
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=" you."))

#do when message reveived
@client.event
async def on_message(message):
    #globals
    global ready, api_endpoint
    #ignore bots
    ##maybe add a second bot that she can talk too at some point                <<<
    if message.author.bot:
        return
    #restrict HourAI to her channels
    ##helper var
    in_channel = False
    if message.channel.id in config_d['CHANNELID']:
        in_channel = True
    ##check if the helper var returned true or not
    if in_channel != True:
        return
    #check for banned users
    if message.author.id in config_d['banned_users']:
        return
    #check for dataset command
    if (message.author.id == config_d['OWNER_ID']) and (message.content == "$DS"):
        output = await build_dataset()
        await message.channel.send(output)
    #sanitize the message
    msg = sanitize_message(message.content)
    #check msg
    if not msg:
        return
    #while the bot is waiting on a response from the model
    #set status as typing for added jazz
    async with message.channel.typing():
        #check if  HF or ShanghAI
        if config_d['ShanghAI']:
            #check that ShanghAI is ready to receive a new query
            if ready:
                #set the ready var to false so that no new queries are sent
                #while ShanghAI is still thinking of a valid response
                ready = False
                #form query payload with the content of the message
                payload = {'inputs': {'text': msg}, 'channel_id': message.channel.id}
                #create the API endpoint for ShanghAI's generate() fucntion
                api_endpoint = config_d['ShanghAI-URL'] + 'generate'
                #send her the input, and store her response
                bot_response = query_ShanghAI(payload, api_endpoint, request_headers)
                #TEST AWAITING:
                #revert the ready state when she has provided a response
                ready = True
        elif config_d['Hugginface']:
            #form query payload with the content of the message
            payload = {'inputs': {'text': msg}}
            #send query to HF and store the response
            response = query_hf(payload, api_endpoint, request_headers)
            #get the 'generated_text' value from the response
            bot_response = response
            if 'estimated_time' in response:
                bot_response = "Loading, please wait {} seconds".format(response["estimated_time"])
            if not bot_response:
                bot_response = "Error, please check terminal."
    #check if user has the roles that allow data collection
    for role in message.author.roles:
        if role.name == 'HourAI Helper':
            #write message so that it can be used later to expand the dataset
            await append_chat_history(message.author.name, msg, bot_response)
    #send the model's response to the Discord channel
    await message.channel.send(bot_response)

client.run(config_d['TOKEN'])
