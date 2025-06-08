#!/bin/bash

# Color Display
clear
echo -e "\e[1;36m====================================================="
echo -e "  \e[1;33mRICK MODS - Forced Bypass"
echo -e "\e[1;36m====================================================="
echo -e "  \e[1;32mYouTube: \e[0mhttps://youtube.com/@rickffmods"
echo -e "  \e[1;32mTelegram 1: \e[0mhttps://t.me/+Cg5m9dujEvZmOTc1"
echo -e "  \e[1;32mTelegram 2: \e[0mhttps://t.me/+fOocns4YX7swODQ1"
echo -e "\e[1;36m=====================================================\e[0m"
echo ""

# Root check
if ! su -c "echo RootCheck" | grep -q "RootCheck"; then
    echo -e "\e[1;31m✗ Root access required!\e[0m"
    exit 1
fi

# IPTables detection
IPTABLES=""
for path in /system/bin/iptables /sbin/iptables /system/xbin/iptables; do
    [ -x "$path" ] && IPTABLES="$path" && break
done
[ -z "$IPTABLES" ] && echo -e "\e[1;31m✗ iptables not found!\e[0m" && exit 1

# Apply forced bypass
echo -e "\e[1;33mApplying Forced Bypass...\e[0m"
su -c "$IPTABLES -F OUTPUT >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -p tcp --dport 80 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d 172.217.0.0/16 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d 142.250.0.0/15 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d 216.58.0.0/15 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d 34.0.0.0/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d 35.0.0.0/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d 91.195.241.232/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d 148.222.67.172/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d 148.222.67.171/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d 148.222.67.170/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d 148.222.67.173/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d 148.222.67.174/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d 148.222.67.169/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d gin.freefireind.in/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d na-gin.freefiremobile.com/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d gin.freefiremobile.com/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d gin.freefire.com/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -d gin.freefire.in/8 -j DROP >/dev/null 2>&1"
su -c "$IPTABLES -A OUTPUT -j ACCEPT >/dev/null 2>&1"
echo -e "\e[1;32m✓ Forced Bypass Applied Successfully\e[0m"

exit 0

  
