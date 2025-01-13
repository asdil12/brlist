#!/usr/bin/python3

import json
import subprocess
import os
import sys

def print_row(col_lens, row, separator='|', space=' ', outer_space=True, limit_col=None, separator_on_extra_rows=True):
    line_length = sum(col_lens) + 3*(len(col_lens)-1) + (2 if outer_space else 0)
    if limit_col != None:
        try:
            termwidth = os.get_terminal_size().columns
            # without this min() the table uses the full term width if limit_col is set
            extra_line_space = min(termwidth - line_length, 0)
            limit_col_max_len = col_lens[limit_col] + extra_line_space
        except:
            limit_col_max_len = col_lens[limit_col]
    else:
        limit_col_max_len = max(col_lens)
    extra_rows = [row]
    for in_extra_row, row in enumerate(extra_rows):
        row_normalized = []
        for i, col in enumerate(row):
            # expand multiline cells to multiple rows
            if isinstance(col, list):
                for c in col[1:]:
                    extra_row = [''] * len(row)
                    extra_row[i] = c
                    #print(extra_row)
                    extra_rows.append(extra_row)
                    #print(extra_rows)
                col = col[0] if col else ''
            if limit_col == i and len(col) > limit_col_max_len:
                col = col[:limit_col_max_len-1] + '…'
            if limit_col == i:
                row_normalized.append(col.ljust(limit_col_max_len, space))
            else:
                row_normalized.append(col.ljust(col_lens[i], space))
        if in_extra_row and not separator_on_extra_rows:
            line = (space * 3).join(row_normalized)
        else:
            line = (space + separator + space).join(row_normalized)
        if outer_space:
            line = space + line + space
        print(line)

def get_col_len(col):
    """
        Returns len of col if col is str - else max col len
    """
    if isinstance(col, list):
        if not col:
            return 0
        return max(map(len, col))
    else:
        return len(col)

def print_table(headers, rows, separator='|', outer_space=True, limit_col=None, separator_on_extra_rows=True):
    col_lens = [get_col_len(hc) for hc in headers or rows[0]]
    for row in rows:
        for i, col_len in enumerate(col_lens):
            col_lens[i] = max(col_len, get_col_len(row[i]))
    if headers:
        print_row(col_lens, headers, separator, outer_space=outer_space, limit_col=limit_col)
        print_row(col_lens, ['']*len(col_lens), '+', '-', outer_space, limit_col=limit_col)
    for row in rows:
        print_row(col_lens, row, separator, outer_space=outer_space, limit_col=limit_col, separator_on_extra_rows=separator_on_extra_rows)


def get_bridges_info():
    bridges = []
    s = subprocess.check_output(["ip", "-d", "-json", "link", "show"])
    interfaces = json.loads(s)
    linux_bridges = {}
    ovs_bridges = {}
    ovs_interfaces = {}
    for interface in interfaces:
        if not 'master' in interface:
            # if interface has no master it IS a master
            if interface.get('linkinfo', {}).get('info_kind') == 'bridge':
                # linux bridge master
                if not interface['ifname'] in linux_bridges.keys():
                    # this ensures that bridges with no slaves will still be listed
                    linux_bridges[interface['ifname']] = {'interfaces': []}
            elif interface.get('linkinfo', {}).get('info_kind') == 'openvswitch':
                # openvswitch bridge master
                ovs_bridges[interface['ifname']] = {
                    "mac": interface['address'],
                    "index": interface['ifindex']
                }
            continue

        # now get the slaves
        if interface['linkinfo']['info_slave_kind'] == 'bridge':
            # linux bridge slave
            if not interface['master'] in linux_bridges:
                linux_bridges[interface['master']] = {'interfaces': []}
            linux_bridges[interface['master']]['interfaces'].append(interface['ifname'])
        elif interface['linkinfo']['info_slave_kind'] == 'openvswitch':
            # openvswitch bride slave
            ovs_interfaces[interface['ifname']] = {"ifname": interface['ifname'], "index": interface['ifindex']}

    # iterate linux bridge masters
    for interface in interfaces:
        if not interface['ifname'] in linux_bridges.keys():
            continue

        # normalize bridge id
        bridge_id = interface['linkinfo']['info_data']['bridge_id']
        prio, _ = bridge_id.split('.')
        prio = int(prio, 16)
        bridge_id = f"{prio:04x}.{interface['address']}"

        br = {
            "ifname": interface['ifname'],
            "index": interface['ifindex'],
            "bridge_type": interface['linkinfo']['info_kind'],
            "mac": interface['address'],
            "bridge_id": bridge_id,
            "stp": "yes" if interface['linkinfo']['info_data']['stp_state'] else "no",
            "interfaces": linux_bridges[interface['ifname']]['interfaces']
        }
        bridges.append(br)


    # openvswitch doesn't report the master<-->slave mapping via iproute2 so let's ask directly
    try:
        ovs_bridges_list = subprocess.check_output(["ovs-vsctl", "list-br"]).decode().strip().split("\n")
    except:
        # ovs is not installed or running
        ovs_bridges_list = []
    for bridge in ovs_bridges_list:
        stp = subprocess.check_output(["ovs-vsctl", "get", "bridge", bridge, "stp_enable"]).decode().strip() == "true"
        rstp = subprocess.check_output(["ovs-vsctl", "get", "bridge", bridge, "rstp_enable"]).decode().strip() == "true"
        if stp:
            bridge_id = subprocess.check_output(["ovs-vsctl", "get", "bridge", bridge, "status:stp_bridge_id"]).decode().strip().strip('"').replace('.', '')
        elif rstp:
            bridge_id = subprocess.check_output(["ovs-vsctl", "get", "bridge", bridge, "rstp_status:rstp_bridge_id"]).decode().strip().strip('"').replace('.', '')
        else:
            bridge_id = ""
        if bridge_id and len(bridge_id) == 16:
            s = bridge_id
            bridge_id = f"{s[0:4]}.{s[4:6]}:{s[6:8]}:{s[8:10]}:{s[10:12]}:{s[12:14]}:{s[14:16]}"

        slaves = []
        # TODO: include all interfaces (like ovs internal gre) on cli flag
        for interface in subprocess.check_output(["ovs-vsctl", "list-ports", bridge]).decode().strip().split("\n"):
            TODO_CMD_FLAG_ALL_OVS_IFS = False
            if interface in ovs_interfaces:
                slaves.append(ovs_interfaces[interface])
            elif TODO_CMD_FLAG_ALL_OVS_IFS:
                slaves.append({"ifname": interface, "index": 999})
        interfaces = [e['ifname'] for e in sorted(slaves, key=lambda e: e['index'])]

        br = {
            "ifname": bridge,
            "bridge_type": "ovs",
            "bridge_id": bridge_id,
            "stp": "yes" if (stp or rstp) else "no",
            "interfaces": interfaces
        }
        br.update(ovs_bridges[bridge]) # fill in mac and ifindex
        bridges.append(br)
    return sorted(bridges, key=lambda e: e['index'])


rows = []
for br in get_bridges_info():
    if len(sys.argv) > 1 and br['ifname'] not in sys.argv[1:]:
        continue
    rows.append([br['ifname'], br['bridge_type'], br['bridge_id'], br['mac'], br['stp'], br['interfaces']])
print_table(["name", "type", "bridge id", "bridge MAC", "STP", "interfaces"], rows, limit_col=2)
