#!/usr/bin/env python
PROGRAM_NAME = "cg-set-wan-bfd.py"
PROGRAM_DESCRIPTION = """
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

"""
from cloudgenix import API, jd
import os
import sys
import argparse

wan_interfaces = {}
CLIARGS = {}
cgx_session = API()              #Instantiate a new CG API Session for AUTH
exclude_hub_sites = True
match_on = "CIRCUIT_NAME"


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=PROGRAM_DESCRIPTION
            )
    parser.add_argument('--token', '-t', metavar='"MYTOKEN"', type=str, 
                    help='specify an authtoken to use for CloudGenix authentication')
    parser.add_argument('--authtokenfile', '-f', metavar='"MYTOKENFILE.TXT"', type=str, 
                    help='a file containing the authtoken')
    parser.add_argument('--matchtext', '-m', metavar='matchtext', type=str, 
                    help='The text to match on', required=True)
    parser.add_argument('--bfd-mode', '-b', metavar='bfdmode', type=str, choices=['aggressive','non_aggressive'],
                    help='The new mode to set (aggressive or nonaggressive)', required=True)
    args = parser.parse_args()
    CLIARGS.update(vars(args)) ##ASSIGN ARGUMENTS to our DICT

def string_match(string, match):
    if str(match).lower() in str(string).lower():
        return True
    return False

def verify_change(prompt):
    answer = None
    print(prompt,"(Y/N)?")
    while answer not in ("yes", "no", "y", "n"):
        answer = input("Enter yes or no: ")
        if string_match(answer,"yes") or string_match(answer,"y"):
            return True
        elif string_match(answer,"no") or string_match(answer,"n"):
            return False
        else:
        	print("Please enter yes or no to verify changes")

def authenticate():
    print("AUTHENTICATING...")
    user_email = None
    user_password = None
    
    ##First attempt to use an AuthTOKEN if defined
    if CLIARGS['token']:                    #Check if AuthToken is in the CLI ARG
        CLOUDGENIX_AUTH_TOKEN = CLIARGS['token']
        print("    ","Authenticating using Auth-Token in from CLI ARGS")
    elif CLIARGS['authtokenfile']:          #Next: Check if an AuthToken file is used
        tokenfile = open(CLIARGS['authtokenfile'])
        CLOUDGENIX_AUTH_TOKEN = tokenfile.read().strip()
        print("    ","Authenticating using Auth-token from file",CLIARGS['authtokenfile'])
    elif "X_AUTH_TOKEN" in os.environ:              #Next: Check if an AuthToken is defined in the OS as X_AUTH_TOKEN
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('X_AUTH_TOKEN')
        print("    ","Authenticating using environment variable X_AUTH_TOKEN")
    elif "AUTH_TOKEN" in os.environ:                #Next: Check if an AuthToken is defined in the OS as AUTH_TOKEN
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
        print("    ","Authenticating using environment variable AUTH_TOKEN")
    else:                                           #Next: If we are not using an AUTH TOKEN, set it to NULL        
        CLOUDGENIX_AUTH_TOKEN = None
        print("    ","Authenticating using interactive login")
    ##ATTEMPT AUTHENTICATION
    if CLOUDGENIX_AUTH_TOKEN:
        cgx_session.interactive.use_token(CLOUDGENIX_AUTH_TOKEN)
        if cgx_session.tenant_id is None:
            print("    ","ERROR: AUTH_TOKEN login failure, please check token.")
            sys.exit()
    else:
        while cgx_session.tenant_id is None:
            cgx_session.interactive.login(user_email, user_password)
            # clear after one failed login, force relogin.
            if not cgx_session.tenant_id:
                user_email = None
                user_password = None            
    print("    ","SUCCESS: Authentication Complete")

def go():
    global exclude_hub_sites
    bfdmode = CLIARGS['bfd_mode']
    match_text = CLIARGS['matchtext']
    ####CODE GOES BELOW HERE#########
    resp = cgx_session.get.tenants()
    if resp.cgx_status:
        tenant_name = resp.cgx_content.get("name", None)
        print("======== TENANT NAME",tenant_name,"========")
    else:
        logout()
        print("ERROR: API Call failure when enumerating TENANT Name! Exiting!")
        print(resp.cgx_status)
        sys.exit((vars(resp)))

    site_count = 0
    
    matched_wan_labels = {}

    ##Generate WAN Interface Labels:
    wan_label_dict = {}
    wan_label_resp = cgx_session.get.waninterfacelabels()
    if wan_label_resp:
        wan_labels = wan_label_resp.cgx_content.get("items", None)
        for label in wan_labels:
            wan_label_dict[label['id']] = {}
            wan_label_dict[label['id']]["name"] = label['name']
            wan_label_dict[label['id']]["label"] = label['label']
            wan_label_dict[label['id']]["description"] = label['description']

    resp = cgx_session.get.sites()
    if resp.cgx_status:
        site_list = resp.cgx_content.get("items", None)    #EVENT_LIST contains an list of all returned events
        for site in site_list:                            #Loop through each EVENT in the EVENT_LIST
            site_count += 1
            
            if (exclude_hub_sites and site['element_cluster_role'] != "HUB"):
                wan_int_resp = cgx_session.get.waninterfaces(site['id'])
                if wan_int_resp:
                    wan_interfaces = wan_int_resp.cgx_content.get("items", None)
                    for interface in wan_interfaces:
                        if (match_on == "CIRCUIT_NAME"):
                            if string_match(interface['name'],match_text):
                                matched_wan_labels[interface['id']] = {}
                                matched_wan_labels[interface['id']]['site_id'] = site['id']
                                matched_wan_labels[interface['id']]['data'] = interface
                                print("Found Circuit Match at SITE:", site['name'])
                                print("  Circuit Name        :",interface['name'])
                                print("  Circuit Category    :",wan_label_dict[interface['label_id']]['name'])
                                print("  Circuit Label       :",wan_label_dict[interface['label_id']]['label'])
                                print("  Circuit Description :",wan_label_dict[interface['label_id']]['description'])
                                print("  Circuit BFD MODE    :",interface['bfd_mode'])
                                
                                print("")
        if(verify_change("This will change all circuits found above to a BFD Mode of " + str(bfdmode) + ", are you sure")):
            print("Changing Sites:")
            print("")
            
            for waninterface in matched_wan_labels:
                print("Site ID:", matched_wan_labels[waninterface]['site_id'], "Current BFD Mode", matched_wan_labels[waninterface]['data']['bfd_mode'],"changing to",bfdmode)
                matched_wan_labels[waninterface]['data']['bfd_mode'] = str(bfdmode)
                site_id = matched_wan_labels[waninterface]['site_id']
                waninterface_id = waninterface
                put_data = matched_wan_labels[waninterface]['data']
                change_wan_bfd_resp = cgx_session.put.waninterfaces(site_id, waninterface_id, put_data)
                if (change_wan_bfd_resp):
                    print(" Success, BFD Mode now", bfdmode)
                else:
                    print(" Failed to make change")
                print("")
        else:
            print("CHANGES ABORTED!")
    else:
        logout()
        print("ERROR: API Call failure when enumerating SITES in tenant! Exiting!")
        sys.exit((jd(resp)))
  
def logout():
    print("Logging out")
    cgx_session.get.logout()

if __name__ == "__main__":
    parse_arguments()
    authenticate()
    go()
    logout()
