ETH Sync Committee

Since the Altair upgrade, 512 validators are randomly chosen every 256 epochs (~27 hours) to form a sync committee. 
Validators in this committee receive much higher rewards. This Python (3.6 or greater) application allows you to check if your validators are
part of the current committee or are due to be part of the next one.

If your beacon node is not at the default address (`http://localhost:5052`), you can change the url/port in the 
`config.ini` file.

Run `eth_sync_committee.py` to launch the application.

Run with `-v/--validators` to specify your validator index(es). You'll be prompted to add it/them to the validators 
file. Once you've added your validator(s) you can run the application without this argument.

Run with `-p/--print-all` to print all of the validators in the current and next sync committees.