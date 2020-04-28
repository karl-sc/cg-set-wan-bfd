CloudGenix Bulk Wan BFD Mode modification script
---------------------------------------
This script will match WAN Interfaces on Circuit Names based on the 
inputted text and modify their BFD value to either Aggressive or Non-Aggressive.

Example Usage:

    python3 cg-set-wan-bfd.py --authtoken ../mytoken.txt -m "lte" -b non-aggressive

This will set all wan interfaces containing the text LTE to a BFD Mode of Non-Aggressive

Matching is done in a case insensitive fasion.

The script will confirm the changes prior to making them

Authentication:
    This script will attempt to authenticate with the CloudGenix controller
    software using an Auth Token or through interactive authentication.
    The authentication selection process happens in the following order:
        1) Auth Token defined via program arguments (--token or -t)
        2) File containing the auth token via program arguments (--authtokenfile or -f)
        3) Environment variable X_AUTH_TOKEN
        4) Environment variable AUTH_TOKEN
        5) Interactive Authentication via terminal
