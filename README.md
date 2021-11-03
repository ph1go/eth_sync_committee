eth_sync_committee.py
=

Since the Altair upgrade, 512 validators are randomly chosen every 256 epochs (~27 hours) to form a sync committee. 
Validators in this committee receive much higher rewards and face much higher penalties for being offline. This Python 
(3.7+) application allows you to check if your validators are part of the current committee or are due to be part of 
the next one and, optionally, be notified by email as soon as one is.

The config file
=
If your beacon node is not at the default address (`http://localhost:5052`), you can change the url/port in the 
`config.ini` file. 

If you'd like to be notified when your validator(s) are in a sync committee, add an email address
and your email password in the `config.ini`, along with the address to send the alerts to. It's only set up for Gmail, I 
recommend creating an email account specifically to send these emails because a) the password is saved as plain text and
b) you need to lessen the account security in order for the script to be able to authenticate with Gmail. To do this, 
you need go into that account's Google Account settings, click on the Security tab and scroll down until you see "Less
secure app access". This needs to be turned on for the email authentication to work.

The idea is that the application is run via a job/task scheduler (eg crontab) and it'll notify you as soon as your 
validator index appears in the current or next sync committee. The sync committees change every ~27 hours so there's
no point checking every minute but a period of an hour will give you plenty of notice.

By default, with the value of `number_of_future_committees` set to 1, 3 sync committees are shown (the current one, the 
next one and the one after). Change the number of sync committees to show after the "next" one with this value. Only the 
validators in the current and next sync committees are known but it might be useful to see the times at which future 
committees occur. 

Running the application
=
Run `eth_sync_committee.py` to launch the application.

Run with `-v/--validators` followed by validator index numbers (separated by a space) to specify your validator index(es). 
You'll be prompted to add it/them to the validators file. Once you've added your validator(s) you can run the application 
without this argument.

Run with `-p/--print-all` to print all of the validators in the current and next sync committees.

Example output
=
     $ ./eth_sync_committee -v 1000 2000 3000 4000 5000 6000 7000 8000 9000

     you've specified validators that aren't in the validators file. would you like to add them? y/n n

     checking validators: 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000 and 9000

                                  epoch    start date & time    validators
     -----------------------------------------------------------------------------------------------------------------------
     sync committee 6 (current)   75776   2021/11/03 07:46:47   none of your validators are in the current sync committee :(
     current epoch (108 of 256)   75884   2021/11/03 19:17:59   n/a
     sync committee 7 (next)      76032   2021/11/04 11:05:11   none of your validators are in the next sync committee :(
     sync committee 8             76288   2021/11/05 14:23:35   validators in this sync committee are not yet known
     sync committee 9             76544   2021/11/06 17:41:59   validators in this sync committee are not yet known