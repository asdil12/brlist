brlist
======

This is a tool to list linux bridges with their member interfaces.
As there is no good replacement for `brctl` in the iproute2 aera,
this tool aims to provide a similar user-friendly output.

```
 bridge name | bridge type | bridge id              | bridge MAC        | STP enabled | interfaces
-------------+-------------+------------------------+-------------------+-------------+------------
 br0         | bridge      | 8000.01:02:03:04:05:ab | 01:02:03:04:05:ab | no          | eth0
             |             |                        |                   |             | eth1
 ovs-system  | openvswitch |                        | 52:a2:f7:f7:ef:7c |             | tap1
             |             |                        |                   |             | tap2
             |             |                        |                   |             | tap3
             |             |                        |                   |             | tap4
             |             |                        |                   |             | tap5
```


Filtering for bridge devices
----------------------------

By calling `brlist` with an arbitrary number of arguments each being
the name of a bridge, the output will be filtered to contain only
those bridges.

```
brlist br0 br2
```

When being called without any arguments `brlist` will show all bridges.
