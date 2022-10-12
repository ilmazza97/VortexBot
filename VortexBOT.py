from telegram.ext import MessageHandler,CommandHandler,Filters,Updater,CallbackQueryHandler
from telegram import InlineKeyboardMarkup,InlineKeyboardButton,InlineKeyboardMarkup,ParseMode
from mysql.connector import connect,Error
import datetime
import re  
import prettytable as pt
import pytz
import smtplib
from email.header import Header
from email.mime.text import MIMEText
import requests
import xmltodict
import os
from csv import writer,reader
import streamlit as st
import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

#region Parameter
CB_ACCOUNT='👤Account'
CB_CHANNELS='🌀Channels'
CB_SERVICES='👨‍💻Services'
CB_LINK='🌐Links'
CB_FREE_TRIAL='🆓Free Trial'
CB_FT_LINK='📍Links'
CB_FT_SCREEN='📲Screen'
#CB_SETTINGS='⚙️Settings'
CB_SUBSCRIPTION='✍️Subcriptions'
CB_DOWNLOAD='📥Download'
CB_FOREX='💎Forex Guide'
CB_BROKER='🏦Broker Guide'
CB_UNSUBSCRIBE='👋Unsubscribe'
CB_REACTIVATE = '😍Reactivate'
FOREX='FOREX VIP ANALYSIS'
GOLD='GOLD VIP Analysis'
updater=None
#endregion

#region Command OK
def start_command(update,context):
    if login(update,context) is False: return
    button(update,context)

def button(update,context):
    chatid=update.effective_chat.id

    keyboard=[]
    keyboard.append([InlineKeyboardButton(text=CB_ACCOUNT,callback_data=CB_ACCOUNT)])     
    keyboard.append([InlineKeyboardButton(text=CB_CHANNELS,callback_data=CB_CHANNELS)])     
    keyboard.append([InlineKeyboardButton(text=CB_SERVICES,callback_data=CB_SERVICES)])  
    keyboard.append([InlineKeyboardButton(text=CB_FREE_TRIAL,callback_data=CB_FREE_TRIAL)])  
    keyboard.append([InlineKeyboardButton(text=CB_LINK,callback_data=CB_LINK)])  
    #keyboard.append([InlineKeyboardButton(text=CB_SETTINGS,callback_data=CB_SETTINGS)])     

    context.bot.send_message(chat_id=chatid,text='👇Choose an option!',reply_markup=InlineKeyboardMarkup(keyboard))

def support_command(update,context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="📩Write to @vort3xsupport")

def services_command(update,context):
    if login(update,context) is False: return

    chatid=update.effective_chat.id
    keyboard=[]
    keyboard.append([InlineKeyboardButton(text='📈Forex VIP Analysis',url='https://vortexproject.net/checkout/?add-to-cart=1232')])
    keyboard.append([InlineKeyboardButton(text='🏆GOLD VIP Analysis',url='https://vortexproject.net/checkout/?add-to-cart=219752')])
    
    context.bot.send_message(chat_id=chatid,text='🫵Our Services!',reply_markup=InlineKeyboardMarkup(keyboard))

def account_command(update,context):
    if login(update,context) is False: return

    chatid=update.effective_chat.id
    keyboard=[]
    keyboard.append([InlineKeyboardButton(text=CB_SUBSCRIPTION,callback_data=CB_SUBSCRIPTION)])     
    keyboard.append([InlineKeyboardButton(text=CB_DOWNLOAD,callback_data=CB_DOWNLOAD)])      

    context.bot.send_message(chat_id=chatid,text='📳Choose an option!',reply_markup=InlineKeyboardMarkup(keyboard))

def vip_command(update,context):
    if login(update,context) is False: return

    chatid=update.effective_chat.id
    keyboard=[]

    result = query(context,'call sp_StatusSubscriptionsShort({})'.format(chatid))
    for row in result:
        keyboard.append([InlineKeyboardButton(text=row[0],url=row[1])]) 
        if row[3] is not None:
            context.bot.unban_chat_member(chat_id=row[2], user_id=2126174292)#chatid)
            query(context,'UPDATE {}TelegramBanMember SET unbandate=now() WHERE id={};'.format(st.secrets['webiste_px'],row[3]))
            db.commit()

    if not keyboard:
        context.bot.send_message(chat_id=chatid,text='⚠️You have no subcription active!')
    else:
        context.bot.send_message(chat_id=chatid,text='🔑Click to enter on VIP Channel!',reply_markup=InlineKeyboardMarkup(keyboard),protect_content=True)

def link_command(update,context):
    chatid=update.effective_chat.id
    keyboard=[]
    keyboard.append([InlineKeyboardButton(text='🏦Roboforex - Broker',url='https://my.roboforex.com/en/?a={}'.format(st.secrets['robo_code']))])
   
    context.bot.send_message(chat_id=chatid,text='🤳Click to register!',reply_markup=InlineKeyboardMarkup(keyboard))

def help_command(update,context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="/start\n/support\n/help")

def send_document(update, context):
    if login(update,context) is False: return

    document = open("Forex Guide - Vortex Project.pdf" if update.callback_query.data==CB_FOREX else "Broker Guide - Vortex Project.pdf", 'rb')
    context.bot.send_document(update.effective_chat.id, document)
#endregion

#region StatusVip OK
def status_command(update,context):
    if login(update,context) is False: return

    chatid=update.effective_chat.id
    result = com(update,context)
    if result is None: return
    markup=[]

    table = pt.PrettyTable(['Subs', 'Next Pay','Renewals','Status'])
    table.align['Services Name'] = 'l'
    table.align['Next Payments'] = 'l'
    table.align['Renewals'] = 'l'
    table.align['Status'] = 'l'

    for row in result:
        table.add_row([row[0].replace(' ANALYSIS',''), f'{row[2]}',f'{row[3]}',f'{row[4]}'])

    markup=[[InlineKeyboardButton(text=CB_UNSUBSCRIBE,callback_data=CB_UNSUBSCRIBE),InlineKeyboardButton(text=CB_REACTIVATE,callback_data=CB_REACTIVATE)]]

    context.bot.send_message(chat_id=chatid,text= f'📝Your active subscriptions\n\n<pre>{table}</pre>',reply_markup=InlineKeyboardMarkup(markup), parse_mode= ParseMode.HTML)

def unsub_reac(update,context,type):
    chatid=update.effective_chat.id
    messageid = update.callback_query.message.message_id
    
    query(context,'CALL sp_UnsubscribeFromBot({},{})'.format(re.sub('.+?_post_id','',update.callback_query.data),type))
    db.commit()

    context.bot.delete_message(chatid, messageid)
    text = '☹️Subcription deleted!' if type==0 else '🤩Subcription reactivated!'
    context.bot.send_message(chat_id=chatid,text=text)

def subs_list(update,context,type):
    chatid=update.effective_chat.id
    result = com(update,context)
    if result is None: return
    markup=[]

    for row in result:
        if row[4]=='Active' and type==0:
            markup.append([InlineKeyboardButton(text=row[0],callback_data='u_post_id{}'.format(row[5]))])
        elif row[4]=='Cancelled' and type==1:
            markup.append([InlineKeyboardButton(text=row[0],callback_data='r_post_id{}'.format(row[5]))])
    
    if(markup is None):
        text= '⚠️There are no services to turn off!' if type==0 else '⚠️There are no services to turn on!'
        context.bot.send_message(chat_id=chatid,text=text)
        return
    
    text = 'Which one would you like to turn off?🤔' if type==0 else 'Which one would you like to turn on?🤔'
    context.bot.send_message(chat_id=chatid,text=text,reply_markup=InlineKeyboardMarkup(markup))
    
def com(update,context):
    chatid=update.effective_chat.id
    
    result = query(context,'call sp_StatusSubscriptions({})'.format(chatid))
    if not result: 
        context.bot.send_message(chat_id=chatid,text='☝️No subcription Active!')
        return
    else:
        return result
#endregion

#region Handle OK
def handle_message(update,context):
    chatid=update.effective_chat.id
    if not login(update,context,False):
        if(re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$',update.effective_message.text)): 

            result = query(context,"select u.id,t.chatid from {0}users u left join {0}Telegram t on t.userid=u.id where u.user_email='{1}';".format(st.secrets['webiste_px'],update.effective_message.text))
           
            for row in result:
                if row[1] is not None:
                    context.bot.send_message(chat_id=chatid,text='♻️The email is already registered!! Use another.')
                    alert(context,"Alert, sospect client!! "+update.effective_chat.id+" ",+update.effective_message.text)
                else:
                    query(context,"INSERT INTO {}Telegram (userid, chatid,username,fullname,language,date) VALUES ({}, {},'{}','{}','{}','{}')".format(st.secrets['webiste_px'],row[0], chatid,update.effective_user.name,update.effective_user.full_name,update.effective_user.language_code,datetime.datetime.now()))                  
                    db.commit()
                    with open(os.path.realpath('Users.csv'), 'a+') as write_obj:
                        csv_writer = writer(write_obj)
                        csv_writer.writerow([chatid])    
                    name = update.effective_chat.username if update.effective_chat.username is not None else update.effective_chat.full_name
                    context.bot.send_message(chat_id=chatid, text="🌀Welcome {}!".format(name))
                    button(update,context)
        else:
            context.bot.send_message(chat_id=chatid,text='⛔Invalid email format! Please insert correctly')
    elif chatid==st.secrets['support_chat_id']:
        mess = update.effective_message.text
        chat_id=update.message.reply_to_message.caption
        if mess.lower()=='ok':
            context.bot.send_message(chat_id=chatid,text='Accepted✅',reply_to_message_id=update.message.reply_to_message.message_id)
            ft_choose_services(chat_id,context)
        elif len(mess.split())>1:
            context.bot.send_message(chat_id=chatid,text='Message sent to costumer✅',reply_to_message_id=update.message.reply_to_message.message_id)     
            context.bot.send_message(chat_id=chat_id,text='👉Message from support: '+mess)
    else:
        result = query(context,"select id from {}FT_Account_Number where chatid={}".format(st.secrets['webiste_px'],chatid))
        if result: 
            context.bot.send_message(chat_id=chatid,text='🙅‍♂️You have already used the free trial.')
            return
        else:
            account_number = update.effective_message.text
            if re.match(r'^([\s\d]+)$', account_number):
                control_robo_account_number(update,context,account_number)
 
def handle_callback_query(update, context):
    chatid=update.effective_chat.id
    if update.callback_query.data==CB_ACCOUNT:
        account_command(update,context)
    elif update.callback_query.data==CB_SUBSCRIPTION:
        status_command(update,context)
    elif update.callback_query.data==CB_DOWNLOAD:
        keyboard=[]
        keyboard.append([InlineKeyboardButton(text=CB_FOREX,callback_data=CB_FOREX)])     
        keyboard.append([InlineKeyboardButton(text=CB_BROKER,callback_data=CB_BROKER)])      
        context.bot.send_message(chat_id=chatid,text='📚Choose your free guide!',reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query.data==CB_FOREX or update.callback_query.data==CB_BROKER:
        send_document(update,context)
    elif update.callback_query.data==CB_CHANNELS:
        vip_command(update,context)
    elif update.callback_query.data==CB_SERVICES:
        services_command(update,context)
    elif update.callback_query.data==CB_LINK:
        link_command(update,context)
    elif update.callback_query.data==CB_FT_SCREEN:
        screen(update,context)
    # elif update.callback_query.data==CB_SETTINGS:
    #     return
    elif update.callback_query.data==CB_UNSUBSCRIBE:
        subs_list(update,context,0)
    elif update.callback_query.data==CB_REACTIVATE: 
        subs_list(update,context,1)
    elif update.callback_query.data==CB_FREE_TRIAL:
        free_trial(update,context)
    elif update.callback_query.data==CB_FT_LINK:
        link_command(update,context)
    elif update.callback_query.data==FOREX or update.callback_query.data==GOLD:
        mess = context.bot.send_message(chat_id=chatid,text='✋Wait a moment')
        query(context,"call sp_CreateFreeTrial({},'{}')".format(update.effective_chat.id,update.callback_query.data))                   
        db.commit()
        context.bot.delete_message(chatid, mess.id)                   
        vip_command(update,context)
    elif update.callback_query.data.startswith('u_post_id'):
        unsub_reac(update,context,0)
    elif update.callback_query.data.startswith('r_post_id'):
        unsub_reac(update,context,1)
    elif update.callback_query.data.startswith('a_post_id'):
        change_to_auto(update,context)
    elif update.callback_query.data.startswith('e_post_id'):
        unsub_reac(update,context,1)

def handle_photo(update, context):
    chatid=update.effective_chat.id
    if login(update,context) is False: return
    result = query(context,"select id from {}FT_Account_Number where chatid={}".format(st.secrets['webiste_px'],chatid))
    if result: 
        context.bot.send_message(chat_id=chatid,text='🙅‍♂️You have already used the free trial')
        return

    name = update.message.photo[-1].file_id
    temp_file=str(name)+'.jpg'
    file = context.bot.getFile(name)
    file.download(temp_file)
    #pio = pytesseract.image_to_string(temp_file)

    context.bot.sendPhoto(chat_id=st.secrets['support_chat_id'], photo=open(temp_file, 'rb'), caption=str(chatid))
    context.bot.sendPhoto(chat_id=chatid,text='📲Your proof of deposit will be checked by our support, you will be notified after validation')
    os.remove(temp_file)
#endregion

#region Job OK
def remove_expired(context):
    result = query(context,'call sp_BanMember()')

    for row in result:
        context.bot.ban_chat_member(chat_id=row[1], user_id=row[0]) 
        query(context,'INSERT INTO {}TelegramBanMember (chatid, linkid, bandate) VALUES ({}}, {}, now());'.format(st.secrets['webiste_px'],row[0],row[2]))
        db.commit()
        context.bot.send_message(chat_id=row[1], text='🦿You have been removed from the channel: {}'.format(row[3])) 

def remind_deadline(context):
    result = query(context,'call sp_RemindDeadline()')

    for row in result:
        if row[2]!='0':
            markup=[[InlineKeyboardButton(text=CB_REACTIVATE,callback_data='e_post_id{}'.format(row[6]))]]
            text='😱Your subscription is about to end and you can no longer be part of the channel\n\n📌Channel Name: *{}*\n📢End Date: *{}*\n⏰Days Left: *{}*\n\n👉If you want to reactivate it, press the pulse below!'.format(row[5],row[2],row[4])
        else:
            markup=[[InlineKeyboardButton(text='🤖Change to auto',callback_data='a_post_id{}'.format(row[6]))]]
            text='😱Your subscription is set for manual payment, remember to pay or you will be removed from the channel\n\n📌Channel Name: *{}*\n💶Next Payment: *{}*\n⏰Days Left: *{}*\n\n👉If you want to turn the payment into auto payment, press the button below!'.format(row[5],row[1],row[3])
        context.bot.send_message(chat_id=row[0], text=text,reply_markup=InlineKeyboardMarkup(markup),parse_mode=ParseMode.MARKDOWN)
        send_email('😱Your subscription is about to end',text,row[7])

def change_to_auto(update,context):
    chatid=update.effective_chat.id
    query(context,'CALL sp_ChangeToAuto({})'.format(re.sub('.+?_post_id','',update.callback_query.data)))
    db.commit()

    messageid = update.callback_query.message.message_id
    context.bot.delete_message(chatid, messageid)
    context.bot.send_message(chat_id=chatid,text='🦾Payment method set to automatic')
#endregion

#region Free Trial OK
def free_trial(update,context):
    chatid=update.effective_chat.id
    keyboard=[]
    keyboard.append([InlineKeyboardButton(text=CB_FT_LINK,callback_data=CB_FT_LINK)])      
    keyboard.append([InlineKeyboardButton(text=CB_FT_SCREEN,callback_data=CB_FT_SCREEN)]) 
    context.bot.send_message(chat_id=chatid,text='👇Choose an option!',reply_markup=InlineKeyboardMarkup(keyboard))
 
def screen(update,context):
    chatid=update.effective_chat.id
    result = query(context,"select id from {}FT_Account_Number where chatid={}".format(st.secrets['webiste_px'],chatid))
    if result: context.bot.send_message(chat_id=chatid,text='🙅‍♂️You have already used the free trial')
    else: context.bot.send_message(chat_id=chatid,text="✍️Enter your broker account number\n\nYou can get it on the broker's website or by checking your emails\n\nExample: 22007000")

def control_robo_account_number(update,context,account_number):
    chatid=update.effective_chat.id

    r = requests.get('https://my.roboforex.com/api/partners?account_id={}&api_key={}'.format(st.secrets['robo_account_id'],st.secrets['robo_api_key']))
    if r.status_code == 200:
        data = xmltodict.parse(r.content)['accounts']
        if data['@count']!='0':
            dica=data['account']
            find=False
            for a in reversed(dica):
                if str(account_number)==a['@id']:
                    find=True
                    query(context,'INSERT INTO {}FT_Account_Number(AccountNumber,ChatId,Platform) VALUES({},{},{});'.format(st.secrets['webiste_px'],account_number,chatid,1))
                    db.commit()    
                    if a['has_reached_deposit_threshold']=='1':
                        ft_choose_services(chatid,context)
                    else:
                        context.bot.send_message(chat_id=chatid,text='📸Please provide us with a screenshot or proof of your deposit!')
                    return
            if not find:
                context.bot.send_message(chat_id=chatid,text='🚨Your account number are not found in the system, please check if you entered it correctly!')

def ft_choose_services(chatid,context):
    keyboard=[]
    keyboard.append([InlineKeyboardButton(text=FOREX,callback_data=FOREX)])
    keyboard.append([InlineKeyboardButton(text=GOLD,callback_data=GOLD)])
    
    context.bot.send_message(chat_id=chatid,text='🤔Choose which channel you want to start the free trial',reply_markup=InlineKeyboardMarkup(keyboard))     
#endregion

#region Other OK
def login(update,context,sendmessage=True):
    chatid=update.effective_chat.id
    if str(chatid) in st.secrets['exclude_chat_id']: return True
    if update.effective_user.language_code=='it':
        context.bot.send_message(chat_id=update.effective_chat.id,text='❌Your country is not enabled')
        return False
    
    with open('Users.csv', 'rt') as f:
        for row in reversed(list(reader(f))):
            if str(chatid) in row[0]:
                return True
            
    result = query(context,"select * from {}Telegram where chatid={};".format(st.secrets['webiste_px'],chatid))
    if not result:
        if sendmessage: context.bot.send_message(chat_id=chatid,text='📨Insert your Website email, to login!')
        return False
    else:
        return True
    
def query(context,select_movies_query):
    try:
        if not db.is_connected(): db.reconnect() 
        with db.cursor() as cursor:
            cursor.execute(select_movies_query)
            result = cursor.fetchall()
            return result
    except Error as err:
        alert(context,err)

def send_email(subject,message,receiver_email):
    sender_email = st.secrets['smtp_username']

    message = MIMEText(message)
    message['Subject'] = subject
    message['From'] = str(Header('🌀Vortex Project <{}}>'.format(sender_email)))
    message['To'] = receiver_email

    server = smtplib.SMTP_SSL(st.secrets['smtp_host'], st.secrets['smtp_port'])
    server.login(sender_email, st.secrets['smtp_password'])
    server.sendmail(sender_email, [receiver_email], message.as_string())
    server.quit()

def alert(context,message):
    context.bot.send_message(chat_id=st.secrets['error_chat_id'], text=message)

def error(update,context):
    alert(context,f"Update {update} caused error {context.error}")
#endregion

def vortex_bot():
    try:    
        dp = updater.dispatcher
        commands = {
            'start': start_command,
            'support': support_command,
            'channels': vip_command,
            'status' : status_command,
            'free' : free_trial,
            'help': help_command,
            'services' : services_command,
            'link' : link_command
        }
        for name, command in commands.items():
            dp.add_handler(CommandHandler(name, command))

        dp.add_handler(MessageHandler(Filters.text,handle_message))
        dp.add_handler(MessageHandler(Filters.photo,handle_photo))
        dp.add_handler(MessageHandler(Filters.document,handle_photo))
        dp.add_handler(CallbackQueryHandler(handle_callback_query))
        dp.add_error_handler(error)
        updater.job_queue.run_daily(remind_deadline,datetime.time(hour=14, minute=00, tzinfo=pytz.timezone('Europe/Rome')))
        updater.job_queue.run_daily(remove_expired,datetime.time(hour=00, minute=00, tzinfo=pytz.timezone('Europe/Rome')))
        
        updater.start_polling()

        print("Vortex Bot started.")
        #updater.idle()
    except Error as e:
        print("Vortex Bot stopped.")
        print(e)
        alert(dp,e)

try:
    updater = Updater(st.secrets['api_token'],use_context=True)
    db = connect(
        host=st.secrets['host'],
        user=st.secrets['user'],
        password=st.secrets['password'],
        database=st.secrets['database'],
    )  
    vortex_bot()
except Error as err:
    alert(updater,err)  
except Exception as ap:
    print(f"ERROR - {ap}")
    exit()