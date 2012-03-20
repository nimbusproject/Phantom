#!/usr/bin/env python


import simplejson as json
import sys


def _make_bools(t):
    if type(t) == dict:
        for k in t:
            t[k] = _make_bools(t[k])
        return t
    elif type(t) == list:
        new_list = []
        for k in t:
            v = _make_bools(k)
            new_list.append(v)
        return new_list
    elif type(t) == str:
        if t.lower() == "false":
            return False
        elif t.lower() == "true":
            return True
        else:
            return t
    else:
        return t


print "configure the provisioner"

provisoner_in_file = "level2/provisioner.json.in"
provisoner_out_file = "level2/provisioner.json"

f = open(provisoner_in_file, "r")
d  = json.load(f)

user_file = "users.txt"
f = open(user_file)
user_list = {}
for l in f:
    l_a = l.split()
    user_list[l_a[0].strip()] = l_a[1].strip()


clouds = {
   'hotel': 'svc.uc.futuregrid.org',
   'sierra': 's83r.idp.sdsc.futuregrid.org',
}

sites = {}
for cloud in clouds:
    name = cloud
    host = clouds[name]

    for user in user_list:
        cloud_site = {}
        cloud_site['driver_class'] = "libcloud.compute.drivers.ec2.NimbusNodeDriver"
        driver_kwargs = {
         'key': user,
         'secret': user_list[user],
         'host': host,
         'port': 8444,
        }
        cloud_site['driver_kwargs'] = driver_kwargs

        site_name = "%s-%s" % (name, user)
        sites[site_name] = cloud_site


d['epuservices']['epu-provisioner-service'][0]['config']['sites'] = sites

d = _make_bools(d)
pout = open(provisoner_out_file, "w")
json.dump(d, pout, indent='    ')

print "configure the phantom"
phantom_in_filename = "level4/phantom_conf.json.in"
phantom_out_filename = "level4/phantom_conf.json"
f = open(phantom_in_filename, "r")
d  = json.load(f)
d['cloudinitdonly']['users'] = user_list
d = _make_bools(d)
pout = open(phantom_out_filename, "w")
json.dump(d, pout, indent='    ')


