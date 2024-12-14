# PyRadioDB
A python project for creating configuration files for trunking radio applications that use software defined radio. Currently uses zeep to interface with the radio reference api to create configuration files. Has a progress indicator, serialization features
, and a search radius feature for getting the strongest signals. Currently only supports SDRTrunk configuration but I am planning on exporting op25 configuration as well.

## Requirements
zeep for accessing the soap api, and tqdm for displaying progress bars.
I believe it works on both windows and linux, maybe even macos.

## Support
It's currently is able to support a majority of digital modes including talkgroups, systems, sites, agencies, analog or narrow fm, usb and lsb, etc.
