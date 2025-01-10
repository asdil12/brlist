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
                col = col[0]
            if limit_col == i and len(col) > limit_col_max_len:
                col = col[:limit_col_max_len-1] + '�[m~@'
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
    bridges = {}
    s = subprocess.check_output(["ip", "-d", "-json", "link", "show"])
    interfaces = json.loads(s)
    for interface in interfaces:
        if not 'master' in interface:
            continue
        if not interface['master'] in bridges:
            bridges[interface['master']] = {'interfaces': []}
        bridges[interface['master']]['interfaces'].append(interface['ifname'])

    for interface in interfaces:
        if not interface['ifname'] in bridges.keys():
            continue
        #print(interface)
        bridge_type = interface['linkinfo']['info_kind']
        bridges[interface['ifname']]['bridge_type'] = bridge_type
        bridges[interface['ifname']]['mac'] = interface['address']
        if bridge_type == 'bridge':
            bridges[interface['ifname']]['bridge_id'] = interface['linkinfo']['info_data']['bridge_id']
            bridges[interface['ifname']]['stp'] = "yes" if interface['linkinfo']['info_data']['stp_state'] else "no"
        else:
            bridges[interface['ifname']]['bridge_id'] = ""
            bridges[interface['ifname']]['stp'] = ""
    return bridges


rows = []
for ifname, br in get_bridges_info().items():
    if len(sys.argv) > 1 and ifname not in sys.argv[1:]:
        continue
    rows.append([ifname, br['bridge_type'], br['bridge_id'], br['mac'], br['stp'], br['interfaces']])
print_table(["bridge name", "bridge type", "bridge id", "bridge MAC", "STP enabled", "interfaces"], rows, limit_col=2)
