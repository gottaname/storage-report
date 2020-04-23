#!/usr/local/bin/python3.7
import smtplib
import subprocess
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

servers = [{"hostname":"","port":"","password":""}
]

def storage_servers():
    info = {}
    for server in servers:
        # check if server is online
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((server['hostname'], int(server['port'])))
        if result == 0:
           # no issue with server, lets continue
           # check zfs array and space.
            try:
                cp = subprocess.run("sshpass -p '" + server['password'] + "' ssh -p " + server['port'] + " " + server['hostname'] +" zpool list -o name,size,allocated,free,health", shell=True, check=True, capture_output=True, universal_newlines=True)
            except subprocess.CalledProcessError as e:
                print(e)
                exit();
            output = cp.stdout
            storage = output.split()
            storage_info = {storage[0]:storage[5],storage[1]:storage[6],storage[2]:storage[7],storage[3]:storage[8],storage[4]:storage[9]}

            try:
                cp = subprocess.run("sshpass -p '" + server['password'] + "' ssh -p " + server['port'] + " " + server['hostname'] +" smbstatus --shares", shell=True, check=True, capture_output=True, universal_newlines=True)
            except subprocess.CalledProcessError as e:
                print(e.stderr)
                exit();
            output = cp.stdout
            smb_systems = output.split('\n')

            # remove the headings
            del smb_systems[:3]
            shares = {}
            users = []
            for smb_system in smb_systems:
                items = smb_system.split()
                if len(items) > 1:
                    if items[0] not in shares:
                        shares[items[0]]= 1
                    else:
                        ct = shares[items[0]]
                        shares[items[0]]= ct + 1
                    if items[2] not in users:
                        users.append(items[2])
            
            info[server['hostname']] = {"status":"Server Up","storage_info":storage_info,"shares":shares,"users":users}
        else:
           info[server['hostname']] = {"status":"Server is down!"}
    return info



# me == my email address
# you == recipient's email address
me = "IT SYSTEMS NOTIFICATION"
you = ['']

def email(servers):
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Storage Systems Status Mailer"
    msg['From'] = me
    msg['To'] = ""

    # Create the body of the message (a plain-text and an HTML version).
    text = ""
    html = """
    <html>
      <head>Storage Server Monitors</head>
      <body>
      """
    for server in servers:
        # general Server info
        info = servers[server]
        html = html + "<div><h1>" + info["storage_info"]["NAME"] + "</h1>"
        if info["storage_info"]["HEALTH"] != "ONLINE":
            html = html + "<b>Status:</b><font color='red'> " + info["storage_info"]["HEALTH"] +"</font><br/>"
        else:
            html = html + "<b>Status:</b><font color='green'> " + info["storage_info"]["HEALTH"] +"</font><br/>"
        html = html + "<b>Total:</b> " + info["storage_info"]["SIZE"] +"<br/>"
        # do percentage usage calculation
        used_percentage = float(info["storage_info"]["ALLOC"][:-1]) / float(info["storage_info"]["SIZE"][:-1]) * 100;
        if used_percentage > 90:
            html = html + "<b>Used:</b><font color='red'> " + info["storage_info"]["ALLOC"] + " (" + str(used_percentage) + "%)</font><br/>"
        elif used_percentage < 90 and used_percentage > 70:
            html = html + "<b>Used:</b><font color='orange'> " + info["storage_info"]["ALLOC"] + " (" + str(used_percentage) + "%)</font><br/>"
        else:
            html = html + "<b>Used:</b><font color='green'> " + info["storage_info"]["ALLOC"] + " (" + str(used_percentage) + "%)</font><br/>"
            
        html = html + "<b>Free:</b> " + info["storage_info"]["FREE"] +"<br/>"
        html = html + "<b>Shares In Use</b><br/>"
        for share in info["shares"]:
            html = html + share + ": " + str(info["shares"][share]) + "<br/>"
        html = html + "<br/><b>IP Addresses using server</b><br/>"
        for ip in info["users"]:
            html = html + ip + "<br/>"
        html = html + "</div>"
        
    html = html + "</body></html>"

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Gmail Sign In
    gmail_sender = ''
    gmail_passwd = ''

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(gmail_sender, gmail_passwd)

    try:
        server.sendmail(me, you, msg.as_string())
        print ('email sent')
    except:
        print ('error sending mail')

    server.quit()

def main():
    servers = storage_servers()
    email(servers)
    
if __name__ == "__main__":
    main()