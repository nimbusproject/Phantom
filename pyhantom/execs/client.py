import boto
from boto.regioninfo import RegionInfo
import boto.ec2.autoscale
import logging
from optparse import OptionParser
import os
import sys
from pyhantom.execs import get_phantom_con
from pyhantom.execs.cmd_opts import bootOpts

def print_display(o, lvl, s):
    print s

def create_lc(commands, argv):
    "Create a new launch configuration"
    u = """%s [options] <launch configuration name> <image name>""" % (argv[1])

    parser = OptionParser(usage=u)

    all_opts = []
    opt = bootOpts("size", "s", "The allocation size", "m1.small")
    all_opts.append(opt)
    opt.add_opt(parser)
    opt = bootOpts("keyname", "k", "The name of the key to use with this launch configuration", None)
    all_opts.append(opt)
    opt.add_opt(parser)
    opt = bootOpts("securitygroup", "g", "The name of the security group to use with this launch configuration", None)
    all_opts.append(opt)
    opt.add_opt(parser)
    opt = bootOpts("userdata", "u", "The user data to associate with this launch configuration", None)
    all_opts.append(opt)
    opt.add_opt(parser)

    (options, args) = parser.parse_args(args=argv[2:])
    if len(args) < 2:
        raise Exception('You must specify a configuration name and an image name')
    lcname = args[0]
    ami = args[1]

    sg = []
    if options.securitygroup:
        sg = [options.securitygroup,]

    con = get_phantom_con()
    lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(con, name=lcname, image_id=ami, key_name=options.keyname, security_groups=sg, user_data=options.userdata, instance_type=options.size)
    con.create_launch_configuration(lc)

    print_display(options, 1, str(lc))


def delete_lc(commands, argv):
    "Delete a launch configuration"
    if len(argv) < 3:
        raise Exception('A launch configuration name is required')
    con = get_phantom_con()
    con.delete_launch_configuration(argv[2])

def list_lc(commands, argv):
    "list all of your launch configurations"

    list_fields = ['name', 'image_id', 'instance_type', "key_name"]
    con = get_phantom_con()
    if len(argv) > 2:
        lcs = con.get_all_launch_configurations(names=argv[2:])
    else:
        lcs = con.get_all_launch_configurations()
    delim = ""
    for f in list_fields:
        msg = "%s%s" % (delim, f)
        sys.stdout.write(msg)
        delim = "\t|\t"
    print ""

    for lc in lcs:
        print dir(lc)
        delim = ""
        for f in list_fields:
            msg = "%s%s" % (delim, lc.__getattribute__(f))
            sys.stdout.write(msg)
            delim = "\t|\t"
        print ""


def create_asg(commands, argv):
    "Create a new autoscale group"
    u = """%s [options] <launch configuration name> <group name> <initial size>""" % (argv[1])

    parser = OptionParser(usage=u)

    all_opts = []
    opt = bootOpts("availabilityzone", "a", "The availabilty zone to use", "us-east")
    all_opts.append(opt)
    opt.add_opt(parser)

    (options, args) = parser.parse_args(args=argv[2:])
    if len(args) < 2:
        raise Exception('You must specify a launch configuration name and a group name')
    lcname = args[0]
    group_name = args[1]
    ds = int(args[2])

    con = get_phantom_con()

    lcs = con.get_all_launch_configurations(names=[lcname,])
    if not lcs and len(lcs) != 1:
        raise Exception('The launch configuration name %s is unknown' % (lcname))
    lc = lcs[0]
    asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=con, group_name=group_name, availability_zones=[options.availabilityzone], min_size=0, max_size=512, desired_capacity=ds)
    con.create_auto_scaling_group(asg)

def list_asg(commands, argv):
    "list all of your epus"

    list_fields = ['availability_zones', 'desired_capacity', 'launch_config_name', 'name',]

    con = get_phantom_con()
    if len(argv) > 2:
        lcs = con.get_all_groups(names=argv[2:])
    else:
        lcs = con.get_all_groups()

    delim = ""
    for f in list_fields:
        msg = "%s%s" % (delim, f)
        sys.stdout.write(msg)
        delim = "  |  "
    print ""
    for lc in lcs:
        delim = ""
        for f in list_fields:
            msg = "%s%s" % (delim, lc.__getattribute__(f))
            sys.stdout.write(msg)
            delim = "  |  "
        print ""
        for i in lc.instances:
            print "\t%s %s %s" % (i.health_status, i.lifecycle_state,i.instance_id)

def delete_asg(commands, argv):
    "delete an EPU"
    if len(argv) < 3:
        raise Exception('A EPU name is required')
    con = get_phantom_con()
    con.delete_auto_scaling_group(argv[2])

def adjust_n(commands, argv):
    "Change the number of VMs preserved in the given group name"
    if len(argv) < 3:
        raise Exception('A EPU name and a new size is required')
    group_name = argv[2]
    c = int(argv[3])

    con = get_phantom_con()
    asg_a = con.get_all_groups(names=[group_name,])
    if not asg_a:
        raise Exception("Group %s not found" % (group_name))
    asg_a[0].set_capacity(c)

def help_commands(commands, argv):
    "Display a list of commands"
    print "This program allows you to control phantom via the AWS autoscale protocol"
    print "The first option must be one of the following commands"

    for c in commands.keys():
        print "%s : %s" % (c, commands[c].__doc__)
        print ''

g_commands = {
    'createlc': create_lc,
    'deletelc': delete_lc,
    'listlc': list_lc,
    'createasg': create_asg,
    'deleteasg': delete_asg,
    'listasg': list_asg,
    'adjustn': adjust_n,
    'help': help_commands,
    '--help': help_commands,
    '-h': help_commands,
}

def main(argv=sys.argv):

    if len(argv) < 2:
        help_commands(g_commands, argv)
    command = argv[1]
    if command not in g_commands.keys():
        print "You have specified an invalid command."
        help_commands(g_commands, argv)

    func = g_commands[command]
    rc = func(g_commands, argv)
    return rc

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
