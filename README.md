# DOsync
Spaces Sync v1.6

Syncs a local folder with a DigitalOcean online Spaces repository.
NOTE: most recently modified file in the local folder will not be uplaoded if UploadSkipLast is flagged

An executable of this program is available at www.ivw.cee.vt.edu

To use:
1) Place DO_config.cfg in the folder C:\DOSync\
2) Modify DO_config.cfg to specify parameters as described below
3) Run program
Log files will be generated in C:\DOSync\log\


DO_config.cfg format:
SyncFolder=local folder to be synced;
SpacesName=name of DigitalOcean space;
AccessKey=access key from DigitalOcean;
SecretAccessKey=secret access key from DigitalOcean;
Region=region of DigitalOcean repository;
Delay=frequency in seconds between syncs;
Extension=file extension types to be synced. Can be a comma-separated list (e.g., .txt,.pdf);
UploadSkipLast=0 or 1, flag for whether to skip the most recently modified file when uploading; See known bugs for v1.6
DoUpload=0 or 1, flag for whether to upload files to DigitalOcean;
DoDownload=0 or 1, flag for whether to download files to DigitalOcean;

Each line must end in a semi-colon. Comments can be made after the semi-colon.


Known bugs/quirks as of v 1.6:

-Fails if there are no files in the droplet.
-Binary flag to skip the last file in case it is still being written is flipped, set to 0 if you want to skip the last file.
-Requires the config file is named DO_config.cfg and is located in C:\DOSync\.
-Sometimes seems to lose connection or access and must be closed and restarted. Not sure why this is or how to fix.
