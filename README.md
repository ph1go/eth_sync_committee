ETH Sync Committee

Since the Altair upgrade, 512 validators are randomly chosen every 256 epochs (~27 hours) to form a sync committee. 
Validators in this committee receive much higher rewards. This application allows you to check if your validators are
part of the current committee or are due to be part of the next one.

Run with `-v/--validators` to specify your validator index(es). You'll be prompted to add it/them to the validators 
file (once you've added your validator(s) you can run the application without this argument.

Run with `-p/--print-all` to print all of the validators in the sync committees.